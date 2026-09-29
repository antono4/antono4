"""Close rollout PRs that contradict the repo owner's own change, and drop their branches.

The owner deliberately removed `.github/workflows/autocommit.yml` from every fork
("chore(ci): hapus auto commit dari fork"), but the rollout had already opened PRs
adding a trigger to that file. Those PRs would re-add the workflow the owner just
removed, so they are closed and their branches deleted.

Non-fork repos are left alone: autocommit.yml still exists there and the PR is valid.
"""

import argparse
import json
import os
import subprocess
import time

BRANCH_NAME = "add-autocommit-workflow-dispatch"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", default=os.environ.get("OWNER", "antono4"))
    p.add_argument("--branch", default=BRANCH_NAME)
    p.add_argument("--dry-run", default=os.environ.get("DRY_RUN", "false"))
    p.add_argument("--min-interval", type=float, default=1.0)
    return p.parse_args()


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


def list_repos(owner):
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
    return repos


def main():
    args = parse_args()
    dry_run = args.dry_run.lower() in ("1", "true", "yes", "on")
    repos = list_repos(args.owner)
    forks = [r for r in repos if r["fork"]]
    print(f"{len(repos)} repos, {len(forks)} forks")

    closed, branches, skipped, errors = 0, 0, 0, []
    for i, repo in enumerate(forks, 1):
        full = repo["full_name"]
        ok, prs = gh([f"/repos/{full}/pulls?state=open&head={args.owner}:{args.branch}"])
        pr_url = None
        if ok and isinstance(prs, list) and prs:
            pr_url = prs[0].get("html_url")
            number = prs[0]["number"]
            if dry_run:
                print(f"  would close {pr_url}")
            else:
                ok2, out = gh(["-X", "PATCH", f"/repos/{full}/pulls/{number}",
                               "-f", "state=closed"], expect_json=False)
                if ok2:
                    closed += 1
                    print(f"  closed {pr_url}")
                else:
                    errors.append((full, f"close failed: {out.splitlines()[0]}"))
                time.sleep(args.min_interval)

        ok, ref = gh([f"/repos/{full}/git/ref/heads/{args.branch}"])
        if ok and isinstance(ref, dict):
            if dry_run:
                print(f"  would delete branch {full}#{args.branch}")
            else:
                ok2, out = gh(["-X", "DELETE", f"/repos/{full}/git/refs/heads/{args.branch}"],
                              expect_json=False)
                if ok2:
                    branches += 1
                else:
                    errors.append((full, f"branch delete failed: {out.splitlines()[0]}"))
                time.sleep(args.min_interval)
        elif not pr_url:
            skipped += 1

        if i % 25 == 0:
            print(f"  ...{i}/{len(forks)}", flush=True)

    print(f"\nPRs closed: {closed}")
    print(f"branches deleted: {branches}")
    print(f"untouched (no PR, no branch): {skipped}")
    if errors:
        print(f"errors: {len(errors)}")
        for full, why in errors[:20]:
            print(f"  {full}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
