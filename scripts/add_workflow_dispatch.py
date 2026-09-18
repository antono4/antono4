"""Add a `workflow_dispatch:` trigger to autocommit.yml across every repo.

`autocommit.yml` ships in every repo with only `push` and `schedule` triggers, so it
cannot be kick-started when GitHub drops or disables its scheduled runs. Adding
`workflow_dispatch:` lets the central routine scheduler re-fire it.

Usage:
    python3 add_workflow_dispatch.py --dry-run          # show what would change
    python3 add_workflow_dispatch.py                    # open one PR per repo

Never commits to a default branch: each repo gets its own branch and PR.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_FILE = ".github/workflows/autocommit.yml"
BRANCH_NAME = "add-autocommit-workflow-dispatch"
TRIGGER_LINE = "  workflow_dispatch:"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", default=os.environ.get("OWNER", "antono4"))
    p.add_argument("--file", default=os.environ.get("TARGET_FILE", TARGET_FILE))
    p.add_argument("--branch", default=os.environ.get("BRANCH_NAME", BRANCH_NAME))
    p.add_argument("--only-repos", default=os.environ.get("ONLY_REPOS") or "")
    p.add_argument("--include-forks", default=os.environ.get("INCLUDE_FORKS", "true"))
    p.add_argument("--include-archived", default=os.environ.get("INCLUDE_ARCHIVED", "false"))
    p.add_argument("--limit", type=int, default=int(os.environ.get("LIMIT") or 0),
                   help="Stop after this many repos (0 = no limit)")
    p.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS") or 6))
    p.add_argument("--dry-run", default=os.environ.get("DRY_RUN", "false"))
    return p.parse_args()


def as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def gh(args, expect_json=True):
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout).strip()
    if not expect_json:
        return True, proc.stdout
    try:
        return True, json.loads(proc.stdout or "null")
    except json.JSONDecodeError:
        return False, "bad json"


def add_trigger(text):
    """Insert `workflow_dispatch:` at the end of the `on:` block.

    Returns (new_text, changed). Raises ValueError if the shape is unrecognised, so a
    surprising file is reported rather than mangled.
    """
    if "workflow_dispatch" in text:
        return text, False

    lines = text.splitlines(keepends=True)
    on_index = None
    for i, line in enumerate(lines):
        if line.rstrip("\n").rstrip() == "on:":
            on_index = i
            break
    if on_index is None:
        raise ValueError("no top-level `on:` line")

    # The block ends at the first non-blank, non-comment line that is not indented.
    end = None
    for j in range(on_index + 1, len(lines)):
        stripped = lines[j].strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not lines[j][:1].isspace():
            end = j
            break
    if end is None:
        raise ValueError("no line after the `on:` block")

    new_lines = lines[:end] + [TRIGGER_LINE + "\n"] + lines[end:]
    return "".join(new_lines), True


def validate(before, after):
    """Confirm the edit only adds `workflow_dispatch` and changes nothing else.

    Compares the parsed documents so the check does not depend on the file having any
    particular set of triggers — plenty of these files have `schedule:` only.
    """
    import yaml
    doc_before = yaml.safe_load(before)
    doc_after = yaml.safe_load(after)

    triggers_after = doc_after.get("on") or doc_after.get(True)
    if not isinstance(triggers_after, dict):
        raise ValueError(f"`on:` is not a mapping: {triggers_after!r}")
    if "workflow_dispatch" not in triggers_after:
        raise ValueError("workflow_dispatch missing after edit")

    triggers_before = doc_before.get("on") or doc_before.get(True)
    if not isinstance(triggers_before, dict):
        raise ValueError(f"original `on:` is not a mapping: {triggers_before!r}")
    lost = set(triggers_before) - set(triggers_after)
    if lost:
        raise ValueError(f"edit dropped existing triggers: {sorted(lost)}")

    # Everything outside `on:` must be identical.
    for doc in (doc_before, doc_after):
        doc.pop("on", None)
        doc.pop(True, None)
    if doc_before != doc_after:
        raise ValueError("edit changed content outside the `on:` block")
    return True


def list_repos(owner, include_forks, include_archived, only_repos):
    repos, page = [], 1
    while True:
        ok, data = gh([f"/user/repos?affiliation=owner&per_page=100&page={page}&sort=full_name"])
        if not ok:
            raise SystemExit(f"failed to list repos: {data}")
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
        allow = {e.split("/")[-1].lower() for e in wanted}
        repos = [r for r in repos if r["name"].lower() in allow]
    return repos


def read_file(full, branch, path):
    ok, data = gh([f"/repos/{full}/contents/{path}?ref={branch}"])
    if not ok or not isinstance(data, dict) or "content" not in data:
        return None
    return base64.b64decode(data["content"]).decode("utf-8", "replace"), data["sha"]


def get_default_branch(full, fallback):
    ok, data = gh([f"/repos/{full}"])
    if ok and isinstance(data, dict) and data.get("default_branch"):
        return data["default_branch"]
    return fallback


def open_pr(item, path, branch_name, dry_run):
    """Create the branch, commit the edit and open the PR for one repo."""
    repo = item["repo"]
    full = repo["full_name"]
    base_branch = item["branch"]
    if dry_run:
        return full, "dry_run", None

    ok, ref = gh([f"/repos/{full}/git/ref/heads/{base_branch}"])
    if not ok or not isinstance(ref, dict):
        return full, "error", f"cannot read base ref: {ref}"
    base_sha = ref["object"]["sha"]

    ok, out = gh(["-X", "POST", f"/repos/{full}/git/refs",
                  "-f", f"ref=refs/heads/{branch_name}",
                  "-f", f"sha={base_sha}"], expect_json=False)
    if not ok:
        if "422" not in out and "already exists" not in out:
            return full, "error", f"cannot create branch: {out.splitlines()[0]}"

    ok, out = gh(["-X", "PUT", f"/repos/{full}/contents/{path}",
                  "-f", "message=Add workflow_dispatch trigger to autocommit.yml",
                  "-f", f"content={base64.b64encode(item['new_text'].encode()).decode()}",
                  "-f", f"branch={branch_name}",
                  "-f", f"sha={item['sha']}"], expect_json=False)
    if not ok:
        return full, "error", f"cannot commit: {out.splitlines()[0]}"

    title = "Add workflow_dispatch trigger to autocommit.yml"
    body = (
        "`autocommit.yml` only declares `push` and `schedule` triggers, so it cannot be "
        "started on demand. GitHub drops scheduled runs under load and disables "
        "`schedule:` in repos that look inactive, which leaves this workflow unable to "
        "run at all.\n\n"
        "This adds a `workflow_dispatch:` trigger so the central routine scheduler in "
        "`antono4/antono4` can re-fire it when its schedule goes quiet.\n\n"
        "---\n\n"
        "*This PR was created by an AI agent (OpenHands) on behalf of antono4.*"
    )
    ok, out = gh(["-X", "POST", f"/repos/{full}/pulls",
                  "-f", f"title={title}",
                  "-f", f"head={branch_name}",
                  "-f", f"base={base_branch}",
                  "-f", f"body={body}"], expect_json=False)
    if not ok:
        if "already exists" in out:
            return full, "pr_exists", None
        return full, "error", f"cannot open PR: {out.splitlines()[0]}"

    try:
        pr_url = json.loads(out).get("html_url")
    except json.JSONDecodeError:
        pr_url = None
    return full, "pr_opened", pr_url


def main():
    args = parse_args()
    dry_run = as_bool(args.dry_run)
    repos = list_repos(args.owner, as_bool(args.include_forks), as_bool(args.include_archived),
                       args.only_repos)
    if args.limit:
        repos = repos[:args.limit]
    print(f"{'would inspect' if dry_run else 'inspecting'} {len(repos)} repos "
          f"for {args.file}")

    plan, problems = [], []
    for i, repo in enumerate(repos, 1):
        full = repo["full_name"]
        base = get_default_branch(full, repo["default_branch"])
        got = read_file(full, base, args.file)
        if got is None:
            problems.append((full, "file unreadable"))
            continue
        text, sha = got
        try:
            new_text, changed = add_trigger(text)
            if changed:
                validate(text, new_text)
        except ValueError as e:
            problems.append((full, f"transform failed: {e}"))
            continue
        if changed:
            plan.append({"full_name": full, "branch": base, "sha": sha,
                         "new_text": new_text, "repo": repo})
        if i % 100 == 0:
            print(f"  inspected {i}/{len(repos)}")

    print(f"\nneeds the trigger: {len(plan)}")
    print(f"already had it / unreadable: {len(repos) - len(plan) - len(problems)}")
    if problems:
        print(f"problems: {len(problems)}")
        for full, why in problems[:20]:
            print(f"  {full}: {why}")

    if not plan:
        print("nothing to do")
        return 0

    print(f"\n{'DRY RUN - no changes will be made' if dry_run else 'opening PRs'}")
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(open_pr, item, args.file, args.branch, dry_run)
            for item in plan
        ]
        for i, fut in enumerate(as_completed(futures), 1):
            results.append(fut.result())
            if not dry_run and i % 25 == 0:
                print(f"  processed {i}/{len(plan)}")
                time.sleep(0.5)

    tally = {}
    for full, status, detail in results:
        tally[status] = tally.get(status, 0) + 1
    print("\nresults:")
    for status, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {status}: {n}")

    opened = [(f, d) for f, s, d in results if s == "pr_opened"]
    if opened:
        print("\nPRs opened:")
        for full, url in sorted(opened):
            print(f"  {full}: {url}")

    failed = [(f, d) for f, s, d in results if s == "error"]
    if failed:
        print("\nerrors:")
        for full, detail in failed[:30]:
            print(f"  {full}: {detail}")

    if os.environ.get("JSON_REPORT"):
        with open(os.environ["JSON_REPORT"], "w") as fh:
            json.dump([{"repo": f, "status": s, "detail": d} for f, s, d in results], fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
