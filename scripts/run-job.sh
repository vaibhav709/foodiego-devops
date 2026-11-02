#!/bin/bash
# Trigger a Jenkins job from the server, e.g.
#   run-job FoodieGo/01-CI-CD-Helm
#   run-job FoodieGo/02-Blue-Green RELEASE=r2 MODE=release
set -euo pipefail
JOB_PATH="/job/$(echo "$1" | sed 's#/#/job/#g')"; shift || true
J=http://localhost:8080; U="admin:$(cat /home/ubuntu/.jenkins-admin)"; CJ=$(mktemp)
CRUMB=$(curl -s -c "$CJ" -u "$U" "$J/crumbIssuer/api/json" | jq -r '.crumbRequestField+":"+.crumb')
if [ $# -gt 0 ]; then
  A=(); for kv in "$@"; do A+=(--data-urlencode "$kv"); done
  curl -sf -b "$CJ" -u "$U" -H "$CRUMB" -X POST "$J$JOB_PATH/buildWithParameters" "${A[@]}"
else
  curl -sf -b "$CJ" -u "$U" -H "$CRUMB" -X POST "$J$JOB_PATH/build"
fi
rm -f "$CJ"; echo "queued: $JOB_PATH $*"
