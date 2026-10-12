// Central place for talking to the system. Everything goes through the
// gateway-service, which is the single entry point into the microservices.
const API_BASE = window.TASKFLOW_API_BASE || "http://localhost:5000/api";

const TaskFlow = {
  getToken() {
    return localStorage.getItem("taskflow_token");
  },
  setSession(token, user) {
    localStorage.setItem("taskflow_token", token);
    localStorage.setItem("taskflow_user", JSON.stringify(user));
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem("taskflow_user") || "null");
    } catch {
      return null;
    }
  },
  clearSession() {
    localStorage.removeItem("taskflow_token");
    localStorage.removeItem("taskflow_user");
  },
  requireAuth() {
    if (!this.getToken()) {
      window.location.href = "index.html";
    }
  },
  async request(path, { method = "GET", body = null, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = this.getToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    }
    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (err) {
      throw new Error("Can't reach the gateway. Is the backend running?");
    }

    let data = null;
    const text = await res.text();
    if (text) {
      try { data = JSON.parse(text); } catch { data = null; }
    }

    if (res.status === 401 && auth) {
      this.clearSession();
      window.location.href = "index.html";
      return;
    }

    if (!res.ok) {
      const message = (data && data.error) || `Request failed (${res.status})`;
      throw new Error(message);
    }
    return data;
  },
  toast(message, isError = false) {
    let el = document.getElementById("tf-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "tf-toast";
      el.className = "toast";
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.className = "toast show" + (isError ? " error" : "");
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove("show"), 3200);
  },
  fmtDate(ts) {
    if (!ts) return "";
    const d = new Date(ts * 1000);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  },
  timeAgo(ts) {
    const diff = Date.now() / 1000 - ts;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  },
};
