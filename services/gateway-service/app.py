import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

SERVICE_NAME = "gateway-service"
PORT = int(os.environ.get("PORT", 5000))

app = Flask(__name__)
CORS(app)

# Maps the first path segment after /api/ to a backend service base URL.
ROUTES = {
    "auth": os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001"),
    "profiles": os.environ.get("USER_SERVICE_URL", "http://localhost:5002"),
    "tasks": os.environ.get("TASK_SERVICE_URL", "http://localhost:5003"),
    "categories": os.environ.get("CATEGORY_SERVICE_URL", "http://localhost:5004"),
    "notifications": os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5005"),
    "analytics": os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:5006"),
    "health": os.environ.get("HEALTH_SERVICE_URL", "http://localhost:5007"),
}

HOP_BY_HOP_HEADERS = {"content-length", "connection", "transfer-encoding", "content-encoding"}


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up", "routes": list(ROUTES.keys())})


@app.route("/api/<prefix>", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/api/<prefix>/<path:subpath>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(prefix, subpath):
    base_url = ROUTES.get(prefix)
    if not base_url:
        return jsonify({"error": f"no service registered for '/api/{prefix}'"}), 404

    target_url = f"{base_url}/{prefix}"
    if prefix == "health":
        target_url = f"{base_url}/all"  # /api/health -> health-service GET /all
    elif subpath:
        target_url = f"{base_url}/{prefix}/{subpath}"

    forward_headers = {k: v for k, v in request.headers if k.lower() not in ("host", "content-length")}

    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            params=request.args,
            data=request.get_data(),
            timeout=8,
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"upstream service unreachable: {exc}"}), 502

    response_headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in HOP_BY_HOP_HEADERS]
    return Response(resp.content, status=resp.status_code, headers=response_headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
