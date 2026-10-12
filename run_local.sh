#!/usr/bin/env bash
# Starts all 8 microservices + a static file server for the frontend.
# Stop everything with: ./stop_local.sh
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
PID_FILE="$ROOT_DIR/.taskflow_pids"
mkdir -p "$LOG_DIR"
> "$PID_FILE"

start_service() {
  local name=$1 port=$2 extra_env=$3
  echo "Starting $name on port $port..."
  (
    cd "$ROOT_DIR/services/$name"
    export PORT=$port
    export JWT_SECRET="taskflow-dev-secret-change-me"
    eval "$extra_env"
    setsid nohup python3 app.py > "$LOG_DIR/$name.log" 2>&1 < /dev/null &
    echo $! >> "$PID_FILE"
  )
}

start_service auth-service 5001 "export USER_SERVICE_URL=http://localhost:5002"
start_service user-service 5002 ""
start_service task-service 5003 "export NOTIFICATION_SERVICE_URL=http://localhost:5005"
start_service category-service 5004 ""
start_service notification-service 5005 ""
start_service analytics-service 5006 "export TASK_SERVICE_URL=http://localhost:5003"
start_service gateway-service 5000 ""
start_service health-service 5007 ""

echo "Starting frontend static server on port 8080..."
(
  cd "$ROOT_DIR/frontend"
  setsid nohup python3 -m http.server 8080 > "$LOG_DIR/frontend.log" 2>&1 < /dev/null &
  echo $! >> "$PID_FILE"
)

sleep 2
echo ""
echo "TaskFlow is up."
echo "  Frontend:      http://localhost:8080"
echo "  Gateway:       http://localhost:5000"
echo "  Service logs:  $LOG_DIR/"
echo ""
echo "Stop everything with: ./stop_local.sh"
