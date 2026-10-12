import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from auth_utils import require_auth

SERVICE_NAME = "task-service"
PORT = int(os.environ.get("PORT", 5003))
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5005")

app = Flask(__name__)
CORS(app)

# In-memory store: {task_id: {...}}
TASKS = {}
NEXT_ID = 1


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up", "tasks_stored": len(TASKS)})


def _serialize(task):
    return task


@app.get("/tasks")
@require_auth
def list_tasks():
    user_id = request.user["user_id"]
    status_filter = request.args.get("status")
    items = [t for t in TASKS.values() if t["user_id"] == user_id]
    if status_filter:
        items = [t for t in items if t["status"] == status_filter]
    items.sort(key=lambda t: t["created_at"], reverse=True)
    return jsonify(items)


@app.post("/tasks")
@require_auth
def create_task():
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    task_id = NEXT_ID
    NEXT_ID += 1
    task = {
        "id": task_id,
        "user_id": request.user["user_id"],
        "title": title,
        "description": (data.get("description") or "").strip(),
        "category_id": data.get("category_id"),
        "status": "pending",
        "due_date": data.get("due_date"),
        "created_at": time.time(),
    }
    TASKS[task_id] = task

    # Service-to-service call: if a due date was set, ask notification-service
    # to create a reminder. Best-effort so task creation never fails because
    # of a downstream hiccup.
    if task["due_date"]:
        try:
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/internal/notifications",
                json={
                    "user_id": task["user_id"],
                    "message": f"Reminder: \"{task['title']}\" is due {task['due_date']}",
                    "type": "reminder",
                },
                timeout=3,
            )
        except requests.RequestException:
            pass

    return jsonify(_serialize(task)), 201


@app.get("/tasks/<int:task_id>")
@require_auth
def get_task(task_id):
    task = TASKS.get(task_id)
    if not task or task["user_id"] != request.user["user_id"]:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)


@app.put("/tasks/<int:task_id>")
@require_auth
def update_task(task_id):
    task = TASKS.get(task_id)
    if not task or task["user_id"] != request.user["user_id"]:
        return jsonify({"error": "task not found"}), 404

    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "category_id", "due_date"):
        if field in data:
            task[field] = data[field]
    if "status" in data and data["status"] in ("pending", "in_progress", "completed"):
        task["status"] = data["status"]

    return jsonify(task)


@app.delete("/tasks/<int:task_id>")
@require_auth
def delete_task(task_id):
    task = TASKS.get(task_id)
    if not task or task["user_id"] != request.user["user_id"]:
        return jsonify({"error": "task not found"}), 404
    del TASKS[task_id]
    return jsonify({"deleted": task_id})


@app.get("/internal/tasks/<int:user_id>")
def internal_tasks_for_user(user_id):
    """Used by analytics-service to compute stats. No auth: trusted internal call."""
    items = [t for t in TASKS.values() if t["user_id"] == user_id]
    return jsonify(items)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
