#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/.taskflow_pids"

if [ ! -f "$PID_FILE" ]; then
  echo "No running TaskFlow processes found (missing $PID_FILE)."
  exit 0
fi

while read -r pid; do
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null && echo "Stopped process $pid"
  fi
done < "$PID_FILE"

rm -f "$PID_FILE"
echo "All TaskFlow processes stopped."
