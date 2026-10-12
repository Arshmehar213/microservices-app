import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from auth_utils import require_auth

SERVICE_NAME = "user-service"
PORT = int(os.environ.get("PORT", 5002))

app = Flask(__name__)
CORS(app)

# In-memory store: {user_id: {user_id, username, display_name, bio, joined_at}}
PROFILES = {}


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up", "profiles": len(PROFILES)})


@app.post("/internal/profiles")
def create_profile():
    """Called by auth-service right after a new user registers."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    PROFILES[str(user_id)] = {
        "user_id": user_id,
        "username": data.get("username", ""),
        "display_name": data.get("display_name") or data.get("username", ""),
        "bio": "",
        "joined_at": time.time(),
    }
    return jsonify(PROFILES[str(user_id)]), 201


@app.get("/profiles/me")
@require_auth
def get_my_profile():
    profile = PROFILES.get(str(request.user["user_id"]))
    if not profile:
        return jsonify({"error": "profile not found"}), 404
    return jsonify(profile)


@app.put("/profiles/me")
@require_auth
def update_my_profile():
    key = str(request.user["user_id"])
    profile = PROFILES.get(key)
    if not profile:
        return jsonify({"error": "profile not found"}), 404

    data = request.get_json(silent=True) or {}
    if "display_name" in data:
        profile["display_name"] = str(data["display_name"])[:80]
    if "bio" in data:
        profile["bio"] = str(data["bio"])[:280]

    return jsonify(profile)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
