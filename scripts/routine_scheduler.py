#!/usr/bin/env python3
"""Run the antono4 routine workflows on a schedule, across every repo.

Each routine already ships with its own `schedule:` cron inside every repo, but those
crons are unreliable: GitHub drops scheduled runs under load, and it silently disables
`schedule:` in repos that look inactive. Some routine files also have no cron at all.

This script is the central safety net. It walks every repo, works out when each routine
last ran, and re-fires the ones that have gone quiet through `workflow_dispatch`.

Workflows that do not declare a `workflow_dispatch:` trigger cannot be fired this way.
They are reported as `not_dispatchable` instead of silently failing.

Requires a token with `repo` + `workflow` scope (a PAT in `ROUTINE_PAT`), because the
default `GITHUB_TOKEN` of one repo cannot dispatch workflows in another.
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

DEFAULT_ROUTINES = [
    "snake.yml",
    "profile-summary-cards.yml",
    "profile-3d.yml",
    "generate-readme.yml",
    "autocommit.yml",
    "auto-update.yml",
    "C3.yml",
    "C2.yml",
    "C1.yml",
]

# After this many repos reject the same routine with 404/422, treat it as missing a
# `workflow_dispatch:` trigger globally and stop spending calls on it.
NON_DISPATCHABLE_AFTER = 5

# How long a routine may go without a run before this scheduler re-fires it. The values
# track each file's own cron: the 10-minute routines only need a nudge when something is
# genuinely wrong, while the daily profile routines are expected to sit idle for a day.
ROUTINE_STALENESS_MINUTES = {
    "snake.yml": 1500,
    "profile-summary-cards.yml": 1500,
    "profile-3d.yml": 1500,
    "generate-readme.yml": 90,
    "autocommit.yml": 90,
    "auto-update.yml": 90,
    "C1.yml": 90,
    "C2.yml": 90,
    "C3.yml": 90,
}
DEFAULT_STALENESS_MINUTES = 90


def as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", default=os.environ.get("OWNER", "antono4"))
    p.add_argument("--mode", choices=["stale", "all", "report"],
                   default=os.environ.get("MODE", "stale"))
    p.add_argument("--staleness-minutes", type=int,
                   default=(int(os.environ["STALENESS_MINUTES"])
                            if os.environ.get("STALENESS_MINUTES") else None),
                   help="Override the staleness threshold for every routine")
    p.add_argument("--routines", default=os.environ.get("ROUTINES") or ",".join(DEFAULT_ROUTINES))
    p.add_argument("--only-repos",
                   default=os.environ.get("ONLY_REPOS") or "",
                   help="Comma-separated repos or owners; blank means every repo")
    p.add_argument("--include-forks", default=os.environ.get("INCLUDE_FORKS", "true"))
    p.add_argument("--include-archived", default=os.environ.get("INCLUDE_ARCHIVED", "false"))
    p.add_argument("--max-dispatch", type=int, default=int(os.environ.get("MAX_DISPATCH") or 300))
    p.add_argument("--api-budget", type=int, default=int(os.environ.get("API_BUDGET") or 4000))
    p.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS") or 8))
    p.add_argument("--dry-run", default=os.environ.get("DRY_RUN", "false"))
    return p.parse_args()


class BudgetExceeded(Exception):
    pass


class Gh:
    """Minimal `gh api` wrapper with a shared call budget."""

    def __init__(self, budget):
        self.remaining = budget

    def __call__(self, args, expect_json=True):
        if self.remaining <= 0:
            raise BudgetExceeded()
        self.remaining -= 1
        try:
            proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return False, "timeout"
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout).strip()
        if not expect_json:
            return True, proc.stdout
        try:
            return True, json.loads(proc.stdout or "null")
        except json.JSONDecodeError:
            return False, "bad json"


def list_repos(gh, owner, include_forks, include_archived, only_repos=""):
    # `/user/repos` is the only listing that includes private repos, but it is scoped to
    # the token's own account. For any other owner fall back to the public listing.
    ok, me = gh(["/user"])
    login = me.get("login", "") if ok and isinstance(me, dict) else ""
    if login and owner.lower() == login.lower():
        listing = "/user/repos?affiliation=owner&per_page=100&page={page}&sort=full_name"
    else:
        listing = f"/users/{owner}/repos?per_page=100&page={{page}}&sort=full_name"

    repos, page = [], 1
    while True:
        ok, data = gh([listing.format(page=page)])
        if not ok:
            raise SystemExit(f"failed to list repos for {owner}: {data}")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    if not include_archived:
        repos = [r for r in repos if not r["archived"]]
    if not include_forks:
        repos = [r for r in repos if not r["fork"]]
    repos = [r for r in repos if not r.get("disabled")]

    wanted = [s.strip() for s in only_repos.split(",") if s.strip()]
    if wanted:
        allow = {entry.split("/")[-1].lower() for entry in wanted}
        repos = [r for r in repos if r["name"].lower() in allow]
    return repos


def thresholds(args, routines):
    if args.staleness_minutes is not None:
        return {name: args.staleness_minutes for name in routines}
    return {name: ROUTINE_STALENESS_MINUTES.get(name, DEFAULT_STALENESS_MINUTES)
            for name in routines}


def age_minutes(created_at, now):
    return (now - datetime.fromisoformat(created_at.replace("Z", "+00:00"))).total_seconds() / 60


def inspect(repo, routines, limits, mode, now, gh):
    full = repo["full_name"]
    res = {
        "repo": full,
        "branch": repo["default_branch"],
        "present": [],
        "ages": {},
        "to_dispatch": [],
        "dispatched": [],
        "dry_run": [],
        "not_dispatchable": [],
        "dispatch_errors": [],
        "skipped_budget": [],
        "unknown": [],
        "error": None,
    }

    ok, data = gh([f"/repos/{full}/actions/workflows?per_page=100"])
    if not ok or not isinstance(data, dict):
        res["error"] = "workflows_unreadable"
        return res
    by_file = {os.path.basename(w["path"]): w for w in data.get("workflows", [])}
    res["present"] = sorted(set(routines) & set(by_file))
    if not res["present"]:
        return res

    # One call usually covers every routine: the repo's most recent runs include the
    # routine runs, since they fire on a short cron.
    last = {}
    ok, data = gh([f"/repos/{full}/actions/runs?per_page=100"])
    if ok and isinstance(data, dict):
        for run in data.get("workflow_runs", []):
            name = os.path.basename(run.get("path", ""))
            if name in routines and name not in last:
                last[name] = run["created_at"]

    for name in res["present"]:
        created = last.get(name)
        if created is None:
            # Busy repos push older runs out of the top-100 window; ask directly.
            try:
                ok, data = gh([f"/repos/{full}/actions/workflows/{name}/runs?per_page=1"])
            except BudgetExceeded:
                res["unknown"].append(name)
                continue
            if ok and isinstance(data, dict):
                runs = data.get("workflow_runs", [])
                created = runs[0]["created_at"] if runs else None
            else:
                res["unknown"].append(name)
                continue

        if created is None:
            # No run on record at all. Treat as stale so the routine gets kick-started,
            # but never on the strength of an unreadable timestamp.
            res["unknown"].append(name)
            if mode != "report":
                res["to_dispatch"].append(name)
            continue

        age = age_minutes(created, now)
        res["ages"][name] = round(age, 1)

        if mode == "all" or (mode == "stale" and age > limits.get(name, DEFAULT_STALENESS_MINUTES)):
            res["to_dispatch"].append(name)

    return res


def fire(res, gh, dry_run, success_left, non_dispatchable, attempts):
    """Dispatch a repo's quiet routines.

    `success_left` is a one-element budget that only successful dispatches consume, so a
    routine that cannot be dispatched never starves the ones that can. `attempts` counts,
    per routine filename, how many repos have rejected it; a routine rejected everywhere
    is dropped early instead of burning an API call in every remaining repo.
    """
    for name in res["to_dispatch"]:
        if name in non_dispatchable:
            res["not_dispatchable"].append(name)
            continue
        if dry_run:
            res["dry_run"].append(name)
            continue
        if success_left[0] <= 0:
            res["skipped_budget"].append(name)
            continue
        try:
            ok, out = gh([
                "-X", "POST",
                f"/repos/{res['repo']}/actions/workflows/{name}/dispatches",
                "-f", f"ref={res['branch']}",
            ], expect_json=False)
        except BudgetExceeded:
            res["skipped_budget"].append(name)
            continue
        if ok:
            success_left[0] -= 1
            attempts[name]["ok"] += 1
            res["dispatched"].append(name)
            continue
        text = out or ""
        if "422" in text or "404" in text:
            attempts[name]["rejected"] += 1
            res["not_dispatchable"].append(name)
            state = attempts[name]
            if state["ok"] == 0 and state["rejected"] >= NON_DISPATCHABLE_AFTER:
                non_dispatchable.add(name)
        else:
            res["dispatch_errors"].append(f"{name}: {text.splitlines()[0] if text else 'error'}")


def write_summary(args, repos, results, dry_run, limits):
    shown = (f"{args.staleness_minutes} min (override)"
             if args.staleness_minutes is not None
             else "per-routine: " + ", ".join(f"`{n}`={v}m" for n, v in sorted(limits.items())))
    lines = [
        "## Routine scheduler",
        "",
        f"- mode: `{args.mode}`",
        f"- staleness thresholds: {shown}",
        f"- repos scanned: **{len(repos)}**",
        f"- routine files found: **{sum(len(r['present']) for r in results)}**",
    ]
    if dry_run:
        lines.append("- **dry run** — nothing dispatched")
    fired = sum(len(r["dispatched"]) + len(r["dry_run"]) for r in results)
    lines.append(f"- routines triggered this pass: **{fired}**")
    errors = [r for r in results if r["error"]]
    if errors:
        lines.append(f"- repos unreadable: **{len(errors)}**")

    coverage = {}
    dispatched = {}
    for res in results:
        for name in res["present"]:
            coverage[name] = coverage.get(name, 0) + 1
        for name in res["dispatched"] + res["dry_run"]:
            dispatched[name] = dispatched.get(name, 0) + 1

    lines += ["", "### Coverage vs. action", "",
              "| routine | repos with file | triggered this pass |", "| --- | --- | --- |"]
    for name in [r.strip() for r in args.routines.split(",") if r.strip()]:
        lines.append(f"| `{name}` | {coverage.get(name, 0)} | {dispatched.get(name, 0)} |")

    triggered = [r for r in results if r["dispatched"] or r["dry_run"]]
    if triggered:
        lines += ["", "### Triggered", ""]
        for res in sorted(triggered, key=lambda r: r["repo"])[:150]:
            names = res["dispatched"] or res["dry_run"]
            lines.append(f"- `{res['repo']}` → " + ", ".join(f"`{n}`" for n in names))
        if len(triggered) > 150:
            lines.append(f"- … and {len(triggered) - 150} more repos")

    nd = {}
    for res in results:
        for name in res["not_dispatchable"]:
            nd.setdefault(name, []).append(res["repo"])
    if nd:
        lines += ["", "### Cannot be dispatched (`workflow_dispatch:` trigger missing)", "",
                  "These keep their own cron but cannot be kick-started. Add a "
                  "`workflow_dispatch:` trigger to the workflow file to bring them under "
                  "this scheduler.", ""]
        for name, reps in sorted(nd.items()):
            lines.append(f"- `{name}` — {len(reps)} repo(s), e.g. {', '.join(reps[:3])}")

    late = [r for r in results if r["skipped_budget"]]
    if late:
        lines += ["", "### Not attempted (dispatch budget reached)", "",
                  f"- {sum(len(r['skipped_budget']) for r in late)} routine(s) across "
                  f"{len(late)} repo(s); the next pass picks them up", ""]

    unk = {}
    for res in results:
        for name in res["unknown"]:
            unk.setdefault(name, []).append(res["repo"])
    if unk:
        lines += ["", "### Timestamp unknown (skipped)", ""]
        for name, reps in sorted(unk.items()):
            lines.append(f"- `{name}` — {len(reps)} repo(s)")

    bad = [r for r in results if r["dispatch_errors"]]
    if bad:
        lines += ["", "### Dispatch errors", ""]
        for res in bad[:50]:
            lines.append(f"- `{res['repo']}`: {'; '.join(res['dispatch_errors'])}")

    if errors:
        lines += ["", "### Repos that could not be read", ""]
        for res in errors[:50]:
            lines.append(f"- `{res['repo']}`: {res['error']}")

    text = "\n".join(lines) + "\n"
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as fh:
            fh.write(text)
    print(text)


def main():
    args = parse_args()
    routines = [r.strip() for r in args.routines.split(",") if r.strip()]
    now = datetime.now(timezone.utc)
    dry_run = as_bool(args.dry_run)

    gh = Gh(args.api_budget)
    limits = thresholds(args, routines)
    repos = list_repos(gh, args.owner, as_bool(args.include_forks), as_bool(args.include_archived),
                       args.only_repos)
    if args.staleness_minutes is not None:
        threshold_desc = f"{args.staleness_minutes}m (override, all routines)"
    else:
        uniq = sorted(set(limits.values()))
        threshold_desc = (f"{uniq[0]}m" if len(uniq) == 1
                          else "per-routine " + ", ".join(f"{n}={v}m" for n, v in sorted(limits.items())))
    print(f"scanning {len(repos)} repos for {len(routines)} routines "
          f"(mode={args.mode}, staleness={threshold_desc}, dry_run={dry_run})")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(inspect, r, routines, limits, args.mode, now, gh)
                   for r in repos]
        for i, fut in enumerate(as_completed(futures), 1):
            results.append(fut.result())
            if i % 100 == 0:
                print(f"  inspected {i}/{len(repos)}")

    results.sort(key=lambda r: r["repo"])

    success_left = [args.max_dispatch]
    non_dispatchable = set()
    attempts = {name: {"ok": 0, "rejected": 0} for name in routines}
    for res in results:
        fire(res, gh, dry_run, success_left, non_dispatchable, attempts)

    for name in sorted(non_dispatchable):
        print(f"note: {name} rejected workflow_dispatch everywhere; "
              f"add a workflow_dispatch trigger to schedule it")

    write_summary(args, repos, results, dry_run, limits)

    if os.environ.get("JSON_REPORT"):
        with open(os.environ["JSON_REPORT"], "w") as fh:
            json.dump(results, fh, indent=1)

    total = sum(len(r["dispatched"]) for r in results)
    print(f"done: {total} workflow dispatches issued")
    return 0


if __name__ == "__main__":
    sys.exit(main())