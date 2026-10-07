#!/usr/bin/env bash
#
# Create (or update) the antono4 routine cron jobs on cron-job.org in one command.
#
# It creates one POST job per routine, staggered by minute offset so the jobs never
# collide on main. Re-running is safe: existing jobs with the same title are updated
# instead of duplicated.
#
# Requirements:
#   - CRONJOB_API_KEY : API key from cron-job.org Console -> Settings.
#   - GITHUB_TOKEN    : fine-grained PAT (Actions: Read and write) or classic PAT
#                       with `repo` + `workflow` scope.
#   - curl, python3
#
# Usage:
#   CRONJOB_API_KEY=xxx GITHUB_TOKEN=ghp_xxx ./create-cron-jobs.sh
#   CRONJOB_API_KEY=xxx GITHUB_TOKEN=ghp_xxx DRY_RUN=1 ./create-cron-jobs.sh
set -euo pipefail

: "${CRONJOB_API_KEY:?CRONJOB_API_KEY is required (cron-job.org Console -> Settings)}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN is required (repo + workflow scope)}"

OWNER="${OWNER:-antono4}"
REPO="${REPO:-antono4}"
REF="${REF:-main}"
DRY_RUN="${DRY_RUN:-0}"
TZ_NAME="${TZ_NAME:-UTC}"

# routine|minute offsets (offset must match the in-repo crons)
ROUTINES=(
  "activity-graph.yml|2,12,22,32,42,52"
  "generate-assets.yml|4,14,24,34,44,54"
  "profile-3d-contrib.yml|6,16,26,36,46,56"
  "profile-stats.yml|8,18,28,38,48,58"
  "autocommit.yml|0,10,20,30,40,50"
)

api="https://api.cron-job.org"
auth="Authorization: Bearer ${CRONJOB_API_KEY}"

existing_json=$(curl -sS -H "$auth" "$api/jobs")

for entry in "${ROUTINES[@]}"; do
  routine="${entry%%|*}"
  minutes_csv="${entry##*|}"
  title="antono4-${routine%.yml}"
  url="https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${routine}/dispatches"

  payload=$(MINUTES_CSV="$minutes_csv" TITLE="$title" URL="$url" REF="$REF" TZ_NAME="$TZ_NAME" \
    GITHUB_TOKEN="$GITHUB_TOKEN" python3 - <<'PY'
import json, os
minutes = [int(m) for m in os.environ["MINUTES_CSV"].split(",")]
job = {
    "title": os.environ["TITLE"],
    "enabled": True,
    "saveResponses": True,
    "url": os.environ["URL"],
    "requestMethod": 1,  # POST
    "extendedData": {
        "headers": {
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
        "body": json.dumps({"ref": os.environ["REF"]}),
    },
    "schedule": {
        "timezone": os.environ["TZ_NAME"],
        "expiresAt": 0,
        "hours": [-1],
        "mdays": [-1],
        "minutes": minutes,
        "months": [-1],
        "wdays": [-1],
    },
}
print(json.dumps({"job": job}))
PY
)

  job_id=$(EXISTING_JSON="$existing_json" TITLE="$title" python3 - <<'PY'
import json, os
data = json.loads(os.environ["EXISTING_JSON"] or "{}")
for j in data.get("jobs", []):
    if j.get("title") == os.environ["TITLE"]:
        print(j["jobId"])
        break
PY
)

  if [ "$DRY_RUN" = "1" ]; then
    if [ -n "$job_id" ]; then
      echo "[dry-run] would UPDATE ${title} (jobId=${job_id}) minutes=${minutes_csv}"
    else
      echo "[dry-run] would CREATE ${title} minutes=${minutes_csv}"
    fi
    continue
  fi

  if [ -n "$job_id" ]; then
    method="PATCH"
    target="$api/jobs/${job_id}"
  else
    method="PUT"
    target="$api/jobs"
  fi

  # cron-job.org allows ~5 write requests/minute, so retry 429 with backoff.
  attempt=1
  max_attempts=6
  while :; do
    code=$(curl -sS -o /tmp/cronjob.out -w '%{http_code}' -X "$method" \
      -H "$auth" -H 'Content-Type: application/json' \
      -d "$payload" "$target")
    if [ "$code" != "429" ]; then
      break
    fi
    if [ "$attempt" -ge "$max_attempts" ]; then
      echo "GAGAL ${title}: masih 429 setelah ${max_attempts} percobaan" >&2
      break
    fi
    wait_s=$((attempt * 15))
    echo "  ${title}: HTTP 429 (rate limit), tunggu ${wait_s}s lalu coba lagi (percobaan $((attempt + 1)))"
    sleep "$wait_s"
    attempt=$((attempt + 1))
  done

  if [ "$method" = "PATCH" ]; then
    echo "updated ${title} (jobId=${job_id}) -> HTTP ${code}"
  else
    echo "created ${title} -> HTTP ${code} $(cat /tmp/cronjob.out)"
  fi
  sleep 2
done

echo
echo "Done. Cek hasilnya di https://console.cron-job.org/jobs"
echo "Test manual: klik job -> 'Test run', atau curl workflow_dispatch langsung."
