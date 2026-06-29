#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/.openclaw/workspace/research/SC_SuperLoop"
RUN_DIR="$ROOT/runs/discovery_public"
PID_FILE="$RUN_DIR/tunnel.pid"
LOG_FILE="$RUN_DIR/tunnel.log"

mkdir -p "$RUN_DIR"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old_pid}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Public discovery tunnel already running on pid $old_pid"
    exit 0
  fi
fi

rm -f "$LOG_FILE"
setsid script -q -c "ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:3091 localhost.run" "$LOG_FILE" < /dev/null > /dev/null 2>&1 &

new_pid=$!
echo "$new_pid" >"$PID_FILE"
sleep 6

if ! kill -0 "$new_pid" 2>/dev/null; then
  echo "Public discovery tunnel failed to stay up; inspect $LOG_FILE" >&2
  exit 1
fi

url="$(grep -Eo 'https://[A-Za-z0-9.-]+' "$LOG_FILE" | grep -v 'https://localhost.run' | tail -n 1 || true)"
if [[ -n "$url" ]]; then
  echo "$url"
else
  echo "Public discovery tunnel started on pid $new_pid but URL not parsed yet" >&2
  exit 1
fi
