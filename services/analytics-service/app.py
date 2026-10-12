import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from auth_utils import require_auth

SERVICE_NAME = "analytics-service"
PORT = int(os.environ.get("PORT", 5006))
TASK_SERVICE_URL = os.environ.get("TASK_SERVICE_URL", "http://localhost:5003")

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up"})


@app.get("/analytics/summary")
@require_auth
def summary():
    user_id = request.user["user_id"]
    try:
        resp = requests.get(f"{TASK_SERVICE_URL}/internal/tasks/{user_id}", timeout=4)
        resp.raise_for_status()
        tasks = resp.json()
    except requests.RequestException:
        return jsonify({"error": "task-service is unavailable, try again shortly"}), 502

    total = len(tasks)
    by_status = {"pending": 0, "in_progress": 0, "completed": 0}
    overdue = 0
    now = time.time()

    for t in tasks:
        status = t.get("status", "pending")
        by_status[status] = by_status.get(status, 0) + 1
        due = t.get("due_date")
        if due and status != "completed":
            try:
                # due_date arrives as an ISO date string (YYYY-MM-DD) from the frontend
                due_ts = time.mktime(time.strptime(due, "%Y-%m-%d"))
                if due_ts < now:
                    overdue += 1
            except ValueError:
                pass

    completion_rate = round((by_status["completed"] / total) * 100, 1) if total else 0.0

    return jsonify(
        {
            "total_tasks": total,
            "by_status": by_status,
            "overdue": overdue,
            "completion_rate": completion_rate,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
