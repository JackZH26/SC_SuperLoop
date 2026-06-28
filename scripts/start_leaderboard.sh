#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/.openclaw/workspace/research/SC_SuperLoop"
LOG_DIR="$ROOT/runs/leaderboard"
PID_FILE="$LOG_DIR/server.pid"
LOG_FILE="$LOG_DIR/server.log"
HEALTH_URL="http://127.0.0.1:3088/api/leaderboard?page=1"

mkdir -p "$LOG_DIR"

is_healthy() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH_URL" || true)"
  [[ "$code" == "200" ]]
}

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old_pid}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    if is_healthy; then
      echo "Leaderboard already healthy on pid $old_pid"
      exit 0
    fi
    echo "Leaderboard process $old_pid is alive but unhealthy; restarting"
    kill "$old_pid" 2>/dev/null || true
    sleep 1
  fi
fi

setsid python3 "$ROOT/leaderboard/server.py" >>"$LOG_FILE" 2>&1 < /dev/null &
new_pid=$!
echo "$new_pid" >"$PID_FILE"

for _ in 1 2 3 4 5; do
  if kill -0 "$new_pid" 2>/dev/null && is_healthy; then
    echo "Leaderboard started healthy on pid $new_pid"
    exit 0
  fi
  sleep 1
done

echo "Leaderboard failed to become healthy; inspect $LOG_FILE" >&2
exit 1
