import os
import time
import requests
from flask import Flask, jsonify
from flask_cors import CORS

SERVICE_NAME = "health-service"
PORT = int(os.environ.get("PORT", 5007))

app = Flask(__name__)
CORS(app)

# Every service in the system, including this one and the gateway.
SERVICES = {
    "gateway-service": os.environ.get("GATEWAY_URL", "http://localhost:5000"),
    "auth-service": os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001"),
    "user-service": os.environ.get("USER_SERVICE_URL", "http://localhost:5002"),
    "task-service": os.environ.get("TASK_SERVICE_URL", "http://localhost:5003"),
    "category-service": os.environ.get("CATEGORY_SERVICE_URL", "http://localhost:5004"),
    "notification-service": os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5005"),
    "analytics-service": os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:5006"),
    "health-service": f"http://localhost:{PORT}",
}


def check_one(name, base_url):
    start = time.perf_counter()
    try:
        resp = requests.get(f"{base_url}/health", timeout=2.5)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        if resp.ok:
            detail = {}
            try:
                detail = resp.json()
            except ValueError:
                pass
            return {
                "name": name,
                "url": base_url,
                "status": "up",
                "latency_ms": latency_ms,
                "detail": detail,
            }
        return {
            "name": name,
            "url": base_url,
            "status": "degraded",
            "latency_ms": latency_ms,
            "detail": {"http_status": resp.status_code},
        }
    except requests.RequestException as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return {
            "name": name,
            "url": base_url,
            "status": "down",
            "latency_ms": latency_ms,
            "detail": {"error": str(exc.__class__.__name__)},
        }


@app.get("/health")
def health():
    return jsonify({"service": SERVICE_NAME, "status": "up"})


@app.get("/all")
def all_statuses():
    results = [check_one(name, url) for name, url in SERVICES.items()]
    up_count = sum(1 for r in results if r["status"] == "up")
    return jsonify(
        {
            "checked_at": time.time(),
            "total_services": len(results),
            "healthy_services": up_count,
            "services": results,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
