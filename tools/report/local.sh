#!/usr/bin/env bash
# Build the four containers, verify them, render the report, and serve it at
# http://localhost:8080 from a read-only nginx container. Nothing is published.
#
#   tools/report/local.sh               # build, verify, render, serve
#   REPORT_PORT=9000 tools/report/local.sh
#   tools/report/local.sh stop          # stop the report server
#
# Needs Docker (with compose) and python3. On Windows run it from WSL or Git Bash.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
COMPOSE="$ROOT/docker/doubly_linked_list/compose.yaml"
PORT="${REPORT_PORT:-8080}"
cd "$ROOT"

if [[ "${1:-}" == "stop" ]]; then
    docker compose -f "$COMPOSE" --profile report down
    exit 0
fi

# Run the gates but keep going if one fails: the report then shows what broke.
status=0
python3 tools/report/collect.py --out report-data/results.json || status=$?
python3 tools/report/build_report.py report-data/results.json --out site

docker compose -f "$COMPOSE" --profile report up -d --force-recreate report
echo
echo "Report:  http://localhost:$PORT"
echo "Raw:     http://localhost:$PORT/results.json"
echo "Stop:    tools/report/local.sh stop"
[[ $status -eq 0 ]] || echo "WARNING: some gates failed (exit $status); the report lists them."
exit "$status"
