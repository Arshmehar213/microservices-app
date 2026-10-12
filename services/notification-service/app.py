import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from auth_utils import require_auth

SERVICE_NAME = "notification-service"
PORT = int(os.environ.get("PORT", 5005))

app = Flask(__name__)
CORS(app)

# In-memory store: {notification_id: {...}}
NOTIFICATIONS = {}
NEXT_ID = 1


@app.get("/health")
def health():
    unread = sum(1 for n in NOTIFICATIONS.values() if not n["read"])
    return jsonify({"service": SERVICE_NAME, "status": "up", "unread": unread})


@app.get("/notifications")
@require_auth
def list_notifications():
    user_id = request.user["user_id"]
    items = [n for n in NOTIFICATIONS.values() if n["user_id"] == user_id]
    items.sort(key=lambda n: n["created_at"], reverse=True)
    return jsonify(items)


@app.post("/internal/notifications")
def internal_create_notification():
    """Called by other services (e.g. task-service) to raise a notification."""
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    message = (data.get("message") or "").strip()
    if user_id is None or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    notification_id = NEXT_ID
    NEXT_ID += 1
    notification = {
        "id": notification_id,
        "user_id": user_id,
        "message": message,
        "type": data.get("type", "info"),
        "read": False,
        "created_at": time.time(),
    }
    NOTIFICATIONS[notification_id] = notification
    return jsonify(notification), 201


@app.patch("/notifications/<int:notification_id>/read")
@require_auth
def mark_read(notification_id):
    notification = NOTIFICATIONS.get(notification_id)
    if not notification or notification["user_id"] != request.user["user_id"]:
        return jsonify({"error": "notification not found"}), 404
    notification["read"] = True
    return jsonify(notification)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
