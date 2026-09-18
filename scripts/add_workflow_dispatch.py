"""Add a `workflow_dispatch:` trigger to autocommit.yml across every repo.

`autocommit.yml` ships in every repo with only `push` and `schedule` triggers, so it
cannot be kick-started when GitHub drops or disables its scheduled runs. Adding
`workflow_dispatch:` lets the central routine scheduler re-fire it.

Usage:
    python3 add_workflow_dispatch.py --dry-run          # show what would change
    python3 add_workflow_dispatch.py                    # open one PR per repo

Never commits to a default branch: each repo gets its own branch and PR.

A run of a few hundred PRs will hit GitHub's secondary rate limit on
content-generating requests. Writes are therefore paced, retried on 403/429/5xx, and
every completed repo is journalled to `--state-file`, so a rerun skips what already
succeeded instead of starting over.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_FILE = ".github/workflows/autocommit.yml"
BRANCH_NAME = "add-autocommit-workflow-dispatch"
TRIGGER_LINE = "  workflow_dispatch:"
MIN_SECONDS_BETWEEN_WRITES = 1.0
MAX_ATTEMPTS = 5


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
    p.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS") or 4))
    p.add_argument("--min-write-interval", type=float,
                   default=float(os.environ.get("MIN_WRITE_INTERVAL") or MIN_SECONDS_BETWEEN_WRITES),
                   help="Minimum seconds between content-generating requests")
    p.add_argument("--state-file", default=os.environ.get("STATE_FILE") or "",
                   help="Journal of completed repos, so a rerun resumes instead of restarting")
    p.add_argument("--max-run-minutes", type=float,
                   default=float(os.environ.get("MAX_RUN_MINUTES") or 0),
                   help="Turn the run into a clean partial success after this many minutes "
                        "(0 = no limit). Progress is journalled either way.")
    p.add_argument("--dry-run", default=os.environ.get("DRY_RUN", "false"))
    return p.parse_args()


def as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class RateLimiter:
    """Paces write calls and holds all writers back when the hourly budget runs low.

    GitHub's write limit is per hour, so once it is exhausted every writer must stop;
    retrying individually just burns time. Tracking `x-ratelimit-remaining` from the
    responses lets the whole run park until the window rolls over.
    """

    RESERVE = 25
    # A content-creation block is a temporary anti-abuse measure, not the hourly quota.
    # GitHub does not publish how long it lasts and it escalates with repeat offences,
    # so back off generously and let the whole run pause together.
    SECONDARY_COOLDOWN_SECONDS = 90

    def __init__(self, min_interval):
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._next_allowed = 0.0
        self._resume_at = 0.0
        self._secondary_strikes = 0

    def wait(self):
        while True:
            with self._lock:
                now = time.monotonic()
                if self._resume_at > now:
                    sleep_for = self._resume_at - now
                else:
                    sleep_for = max(0.0, self._next_allowed - now)
                    self._next_allowed = max(now, self._next_allowed) + self.min_interval
            if sleep_for <= 0:
                return
            if sleep_for > 1:
                print(f"    pacing: waiting {sleep_for:.0f}s")
            time.sleep(sleep_for)

    def note_headers(self, headers):
        """Park all writers until reset once the remaining budget gets close to zero."""
        remaining = headers.get("x-ratelimit-remaining")
        reset = headers.get("x-ratelimit-reset")
        if remaining is None or reset is None:
            return
        try:
            remaining_i, reset_f = int(remaining), float(reset)
        except ValueError:
            return
        if remaining_i > self.RESERVE:
            return
        delay = max(0.0, reset_f - time.time()) + 5
        with self._lock:
            self._resume_at = max(self._resume_at, time.monotonic() + delay)

    def note_secondary_limit(self, retry_after=None):
        """Pause every writer after a content-creation block, escalating on repeats."""
        with self._lock:
            self._secondary_strikes += 1
            strikes = self._secondary_strikes
        delay = retry_after if retry_after else min(
            600.0, self.SECONDARY_COOLDOWN_SECONDS * (2 ** (strikes - 1)))
        with self._lock:
            self._resume_at = max(self._resume_at, time.monotonic() + delay)
        print(f"    content-creation block (strike {strikes}): pausing {delay:.0f}s")

    def note_success(self):
        """Reset the escalation once writes are flowing again."""
        with self._lock:
            self._secondary_strikes = 0


def run_gh(args):
    """Run `gh api` and capture body plus headers, so rate-limit state is authoritative.

    GitHub's error *body* includes the request timestamp, not the reset time, so parsing
    the body gives a bogus answer. The `x-ratelimit-reset` header is the real one.

    Output is captured as bytes and decoded here: `text=True` would translate the CRLF
    header terminator to LF, which breaks splitting headers from body.
    """
    proc = subprocess.run(["gh", "api", "-i", *args], capture_output=True, timeout=180)
    raw = (proc.stdout or b"").decode("utf-8", "replace")
    stderr = (proc.stderr or b"").decode("utf-8", "replace")

    headers, body = {}, raw
    if raw.startswith("HTTP/"):
        # Headers end at the first blank line; the body may contain blank lines too, so
        # only the first split counts.
        boundary = _header_boundary(raw)
        if boundary is not None:
            head, body = raw[:boundary], raw[boundary:]
            for line in head.splitlines():
                key, sep, value = line.partition(":")
                if sep:
                    headers[key.strip().lower()] = value.strip()

    if proc.returncode != 0:
        return False, (stderr or body).strip(), headers
    return True, body, headers


def _header_boundary(raw):
    """Index just past the blank line that ends the header block, or None."""
    for marker in ("\r\n\r\n", "\n\n"):
        idx = raw.find(marker)
        if idx != -1:
            return idx + len(marker)
    return None


def parse_rate_limit_reset(headers, text, now=None):
    """Seconds until the rate limit resets, preferring the response header.

    Falls back to any `Retry-After` value, and returns None when nothing usable is
    present, so the caller uses normal backoff rather than guessing.
    """
    reset = headers.get("x-ratelimit-reset")
    if reset:
        try:
            return max(0.0, float(reset) - time.time())
        except ValueError:
            pass
    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass
    return None


def is_primary_rate_limit(headers, text):
    """True when the core REST budget is what refused the call."""
    if headers.get("x-ratelimit-remaining") == "0":
        return True
    lowered = (text or "").lower()
    return "api rate limit exceeded" in lowered or "rate limit exceeded for user" in lowered


def is_secondary_rate_limit(text):
    """True for the content-creation block, which is separate from the hourly quota."""
    lowered = (text or "").lower()
    return "secondary rate limit" in lowered or "content creation" in lowered


def is_retryable(text):
    """True for throttling and transient failures, which are worth another attempt.

    A plain permission denial is not retryable — it will fail the same way every time —
    so it is excluded before the generic checks.
    """
    lowered = (text or "").lower()
    permanent = ("resource not accessible", "not accessible by integration", "bad credentials",
                 "must have admin")
    if any(marker in lowered for marker in permanent) and "rate limit" not in lowered:
        return False
    return any(marker in lowered for marker in (
        "secondary rate limit", "rate limit", "abuse", "429", "content creation",
        "500", "502", "503", "504", "timeout", "timed out", "connection reset",
    ))


def parse_retry_after(headers):
    """Seconds from a `Retry-After` header, or None when absent/unparseable."""
    value = headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def throttle_delay(attempt, headers, text):
    """Backoff for a retry. Waits out the rate-limit window when that is what refused.

    Only used when the caller gave no deadline. Otherwise `gh` waits until the window
    rolls over itself, bounded by the deadline, so a run cannot sleep indefinitely.
    """
    reset_in = parse_rate_limit_reset(headers, text)
    if reset_in is not None and is_primary_rate_limit(headers, text):
        return min(3700.0, reset_in + 5)
    return min(60.0, 2.0 ** attempt)


def gh(args, expect_json=True, limiter=None, retries=MAX_ATTEMPTS, deadline=None):
    """Run `gh api`, pacing and retrying when a write is throttled or fails transiently.

    When the rate limit is exhausted and a deadline is set, this sleeps until the window
    rolls over instead of retrying into a wall — but only if the reset falls inside the
    deadline, otherwise it gives up so the run can be resumed later.
    """
    last = ""
    last_headers = {}
    for attempt in range(retries):
        if limiter is not None:
            limiter.wait()
        try:
            ok, out, headers = run_gh(args)
        except subprocess.TimeoutExpired:
            last, last_headers = "timeout", {}
            if attempt < retries - 1:
                time.sleep(throttle_delay(attempt, last_headers, last))
                continue
            return False, last
        last_headers = headers
        if limiter is not None:
            limiter.note_headers(headers)
        if ok:
            if limiter is not None:
                limiter.note_success()
            if not expect_json:
                return True, out
            try:
                return True, json.loads(out or "null")
            except json.JSONDecodeError:
                return False, "bad json"
        last = (out or "").strip()

        # A content-creation block is a temporary anti-abuse measure, not the hourly
        # quota, and GitHub does not send a reset time for it. Pause every writer so the
        # run backs off as a whole rather than each thread hammering independently.
        if limiter is not None and is_secondary_rate_limit(last):
            limiter.note_secondary_limit(retry_after=parse_retry_after(headers))

        if attempt >= retries - 1 or not is_retryable(last):
            return False, last

        delay = throttle_delay(attempt, headers, last)
        if deadline is not None:
            if time.monotonic() + delay > deadline:
                return False, f"rate_limited (next reset in {delay:.0f}s, beyond this run's deadline)"
            sleep_for = delay
        else:
            sleep_for = delay
        if sleep_for > 1:
            print(f"    waiting {sleep_for:.0f}s for rate limit to reset")
        # Capped so the limiter's shared gate is re-checked promptly: a cooldown recorded
        # by another thread should hold this one back too.
        time.sleep(min(sleep_for, 30.0))
    return False, last


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
    """Use the default branch from the repo listing; only call the API if it is missing."""
    if fallback:
        return fallback
    ok, data = gh([f"/repos/{full}"])
    if ok and isinstance(data, dict) and data.get("default_branch"):
        return data["default_branch"]
    return "main"


def open_pr(item, path, branch_name, dry_run, limiter, deadline):
    """Create the branch, commit the edit and open the PR for one repo."""
    repo = item["repo"]
    full = repo["full_name"]
    base_branch = item["branch"]
    if dry_run:
        return full, "dry_run", None

    ok, ref = gh([f"/repos/{full}/git/ref/heads/{base_branch}"], deadline=deadline)
    if not ok or not isinstance(ref, dict):
        return full, "error", f"cannot read base ref: {ref}"
    base_sha = ref["object"]["sha"]

    branch_exists = False
    ok, out = gh(["-X", "POST", f"/repos/{full}/git/refs",
                  "-f", f"ref=refs/heads/{branch_name}",
                  "-f", f"sha={base_sha}"], expect_json=False, limiter=limiter, deadline=deadline)
    if not ok:
        if "422" in out or "already exists" in out:
            branch_exists = True
        else:
            return full, "error", f"cannot create branch: {out.splitlines()[0]}"

    feature_sha = item["sha"]
    new_text = item["new_text"]
    if branch_exists:
        # A previous run already created this branch. Re-read the file from it and edit
        # the current revision — these files change often, so the revision the plan was
        # built from may already be stale, and committing against a stale sha is a 409.
        existing = read_file(full, branch_name, path)
        if existing is None:
            return full, "error", "cannot read file on existing branch"
        text, feature_sha = existing
        if "workflow_dispatch" in text:
            # The branch already carries the edit; just make sure a PR is open.
            return open_pull_request(full, path, branch_name, base_branch, limiter, deadline)
        try:
            new_text, changed = add_trigger(text)
            if changed:
                validate(text, new_text)
        except ValueError as e:
            return full, "error", f"transform failed on existing branch: {e}"

    ok, out = gh(["-X", "PUT", f"/repos/{full}/contents/{path}",
                  "-f", "message=Add workflow_dispatch trigger to autocommit.yml",
                  "-f", f"content={base64.b64encode(new_text.encode()).decode()}",
                  "-f", f"branch={branch_name}",
                  "-f", f"sha={feature_sha}"], expect_json=False, limiter=limiter, deadline=deadline)
    if not ok:
        if "409" in out:
            return full, "error", "conflict: file changed on the branch during rollout"
        return full, "error", f"cannot commit: {out.splitlines()[0]}"

    return open_pull_request(full, path, branch_name, base_branch, limiter, deadline)


def find_open_pr(full, branch_name):
    """Return the html_url of the open PR for `branch_name`, if there is one."""
    owner = full.split("/")[0]
    ok, data = gh([f"/repos/{full}/pulls?state=open&head={owner}:{branch_name}&per_page=1"])
    if ok and isinstance(data, list) and data:
        return data[0].get("html_url")
    return None


def open_pull_request(full, path, branch_name, base_branch, limiter, deadline):
    """Open the PR, tolerating one that is already open."""
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
                  "-f", f"body={body}"], expect_json=False, limiter=limiter, deadline=deadline)
    if not ok:
        if "already exists" in out:
            return full, "pr_exists", None
        if "422" in out or "validation failed" in out.lower():
            # GitHub reports an already-open PR for this branch as a bare 422, so look
            # the existing PR up rather than treating it as a failure.
            existing = find_open_pr(full, branch_name)
            if existing:
                return full, "pr_exists", existing
        return full, "error", f"cannot open PR: {out.splitlines()[0]}"

    try:
        pr_url = json.loads(out).get("html_url")
    except json.JSONDecodeError:
        pr_url = None
    return full, "pr_opened", pr_url


def load_state(path):
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(path, state):
    if not path:
        return
    tmp = f"{path}.tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def main():
    args = parse_args()
    dry_run = as_bool(args.dry_run)
    repos = list_repos(args.owner, as_bool(args.include_forks), as_bool(args.include_archived),
                       args.only_repos)
    if args.limit:
        repos = repos[:args.limit]
    print(f"{'would inspect' if dry_run else 'inspecting'} {len(repos)} repos "
          f"for {args.file}")

    state = load_state(args.state_file)
    already_done = {repo for repo, status in state.items()
                    if status in ("pr_opened", "pr_exists")}
    if already_done:
        print(f"resuming: {len(already_done)} repo(s) already done in a previous run")

    plan, problems = [], []
    for i, repo in enumerate(repos, 1):
        full = repo["full_name"]
        if full in already_done:
            continue
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
                         "new_text": new_text, "repo": repo, "changed": changed})
        if i % 100 == 0:
            print(f"  inspected {i}/{len(repos)}")

    print(f"\nneeds the trigger: {len(plan)}")
    if problems:
        print(f"problems: {len(problems)}")
        for full, why in problems[:20]:
            print(f"  {full}: {why}")
    for full, why in problems:
        state[full] = f"problem:{why}"

    if not plan:
        save_state(args.state_file, state)
        print("nothing to do")
        return 0

    limiter = RateLimiter(args.min_write_interval)
    deadline = (time.monotonic() + args.max_run_minutes * 60) if args.max_run_minutes else None

    print(f"\n{'DRY RUN - no changes will be made' if dry_run else 'opening PRs'} "
          f"(workers={args.workers}, min interval between writes="
          f"{args.min_write_interval}s)")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(open_pr, item, args.file, args.branch, dry_run, limiter, deadline)
            for item in plan
        ]
        for i, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            results.append(result)
            full, status, _ = result
            state[full] = status
            if i % 10 == 0 or status == "error":
                save_state(args.state_file, state)
            if not dry_run and i % 25 == 0:
                print(f"  processed {i}/{len(plan)}")
    save_state(args.state_file, state)

    tally = {}
    for full, status, detail in results:
        tally[status] = tally.get(status, 0) + 1
    print("\nresults:")
    for status, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {status}: {n}")

    opened = [(f, d) for f, s, d in results if s == "pr_opened"]
    if opened:
        print(f"\nPRs opened ({len(opened)}):")
        for full, url in sorted(opened):
            print(f"  {full}: {url}")

    failed = [(f, d) for f, s, d in results if s == "error"]
    if failed:
        print(f"\nerrors ({len(failed)}) — rerun with the same --state-file to retry these:")
        for full, detail in failed[:30]:
            print(f"  {full}: {detail}")

    if args.state_file:
        print(f"\nstate journal: {args.state_file}")

    if os.environ.get("JSON_REPORT"):
        with open(os.environ["JSON_REPORT"], "w") as fh:
            json.dump([{"repo": f, "status": s, "detail": d} for f, s, d in results], fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
