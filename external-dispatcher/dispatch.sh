#!/usr/bin/env bash
#
# Dispatch one routine workflow on a 10-minute cadence from any machine with cron.
#
# Usage (add to `crontab -e`, staggered so the routines never collide):
#   */10 * * * *  GITHUB_TOKEN=ghp_xxx OWNER=antono4 REPO=antono4 /path/dispatch.sh activity-graph.yml
#   2-59/10 * * * *  ... /path/dispatch.sh generate-assets.yml
#
# Requires: curl. The token needs `repo` + `workflow` scope (or Actions: write on a
# fine-grained PAT scoped to the repo). Never commit the token.
set -euo pipefail

ROUTINE="${1:?usage: dispatch.sh <workflow-file.yml>}"
OWNER="${OWNER:-antono4}"
REPO="${REPO:-antono4}"
REF="${REF:-main}"

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"

url="https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${ROUTINE}/dispatches"

code=$(curl -sS -o /tmp/dispatch.out -w '%{http_code}' -X POST "$url" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d "{\"ref\":\"${REF}\"}")

if [ "$code" = "204" ]; then
  echo "$(date -u +%FT%TZ) dispatched ${ROUTINE} (${code})"
else
  echo "$(date -u +%FT%TZ) failed to dispatch ${ROUTINE} (${code}): $(cat /tmp/dispatch.out)" >&2
  exit 1
fi
