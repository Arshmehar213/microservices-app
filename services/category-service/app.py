import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from auth_utils import require_auth

SERVICE_NAME = "category-service"
PORT = int(os.environ.get("PORT", 5004))

app = Flask(__name__)
CORS(app)

# In-memory store: {category_id: {...}}
CATEGORIES = {}
NEXT_ID = 1

DEFAULT_COLORS = ["#2DD4BF", "#F59E0B", "#818CF8", "#F87171", "#34D399", "#EC4899"]


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up", "categories": len(CATEGORIES)})


@app.get("/categories")
@require_auth
def list_categories():
    user_id = request.user["user_id"]
    items = [c for c in CATEGORIES.values() if c["user_id"] == user_id]
    items.sort(key=lambda c: c["created_at"])
    return jsonify(items)


@app.post("/categories")
@require_auth
def create_category():
    global NEXT_ID
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    user_id = request.user["user_id"]
    existing_count = sum(1 for c in CATEGORIES.values() if c["user_id"] == user_id)

    category_id = NEXT_ID
    NEXT_ID += 1
    category = {
        "id": category_id,
        "user_id": user_id,
        "name": name,
        "color": data.get("color") or DEFAULT_COLORS[existing_count % len(DEFAULT_COLORS)],
        "created_at": time.time(),
    }
    CATEGORIES[category_id] = category
    return jsonify(category), 201


@app.delete("/categories/<int:category_id>")
@require_auth
def delete_category(category_id):
    category = CATEGORIES.get(category_id)
    if not category or category["user_id"] != request.user["user_id"]:
        return jsonify({"error": "category not found"}), 404
    del CATEGORIES[category_id]
    return jsonify({"deleted": category_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
