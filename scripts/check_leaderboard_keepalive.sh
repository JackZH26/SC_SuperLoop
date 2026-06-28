#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/.openclaw/workspace/research/SC_SuperLoop"
URL="http://127.0.0.1:3088/api/leaderboard?page=1"
LOG_FILE="$ROOT/runs/leaderboard/server.log"

check_code() {
  curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL" || true
}

code="$(check_code)"
if [[ "$code" == "200" ]]; then
  echo "leaderboard healthy: 200"
  exit 0
fi

bash "$ROOT/scripts/start_leaderboard.sh"

for _ in 1 2 3; do
  sleep 2
  code="$(check_code)"
  if [[ "$code" == "200" ]]; then
    echo "leaderboard recovered: 200"
    exit 0
  fi
done

echo "leaderboard unhealthy after restart: ${code:-unknown}" >&2
if [[ -f "$LOG_FILE" ]]; then
  tail -n 40 "$LOG_FILE" >&2
fi
exit 1
