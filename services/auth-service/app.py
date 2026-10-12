import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from auth_utils import create_token, require_auth

SERVICE_NAME = "auth-service"
PORT = int(os.environ.get("PORT", 5001))
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://localhost:5002")

app = Flask(__name__)
CORS(app)

# In-memory store for demo purposes: {username: {id, username, password_hash}}
USERS = {}
NEXT_ID = 1


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up", "users_registered": len(USERS)})


@app.post("/auth/register")
def register():
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or username).strip()

    if len(username) < 3:
        return jsonify({"error": "username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400
    if username in USERS:
        return jsonify({"error": "username already taken"}), 409

    user_id = NEXT_ID
    NEXT_ID += 1
    USERS[username] = {
        "id": user_id,
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": time.time(),
    }

    # Service-to-service call: ask user-service to create the default profile.
    # Best-effort -- registration still succeeds even if user-service is down.
    try:
        requests.post(
            f"{USER_SERVICE_URL}/internal/profiles",
            json={"user_id": user_id, "username": username, "display_name": display_name},
            timeout=3,
        )
    except requests.RequestException:
        pass

    token = create_token(user_id, username)
    return jsonify({"token": token, "user": {"id": user_id, "username": username}}), 201


@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = USERS.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid username or password"}), 401

    token = create_token(user["id"], user["username"])
    return jsonify({"token": token, "user": {"id": user["id"], "username": user["username"]}})


@app.get("/auth/verify")
@require_auth
def verify():
    # Lets other parts of the system (or curious frontends) confirm a token is valid.
    return jsonify({"valid": True, "user": request.user})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
