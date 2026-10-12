# TaskFlow

A small task-management app built as a real microservices system — 8 independent
Flask services behind a gateway, plus a plain HTML/CSS/JS frontend with a live
service-status page.

## Architecture

```
                        ┌──────────────────┐
                        │     frontend      │  (static HTML/CSS/JS, :8080)
                        └─────────┬─────────┘
                                  │  /api/*
                        ┌─────────▼─────────┐
                        │  gateway-service   │  :5000  — routes requests
                        └─────────┬─────────┘
          ┌───────────┬───────────┼───────────┬───────────┬───────────┐
          │            │           │           │           │           │
    ┌─────▼────┐ ┌─────▼────┐┌─────▼────┐┌─────▼──────┐┌───▼────────┐┌─▼──────────┐
    │  auth    │ │  user    ││  task    ││  category  ││notification││ analytics  │
    │ :5001    │ │ :5002    ││ :5003    ││ :5004      ││ :5005      ││ :5006      │
    └─────┬────┘ └────▲─────┘└────┬─────┘└────────────┘└─────▲──────┘└─────▲──────┘
          │           │           │                          │             │
          └───────────┘           └──────────────────────────┘             │
     (creates profile on            (creates a reminder when         (reads tasks to
      registration)                  a task gets a due date)          compute stats)

                        ┌───────────────────┐
                        │  health-service    │  :5007 — pings every
                        │                    │  service's /health
                        └────────────────────┘
```

Each service owns its own in-memory data (swap in a real database per service
for production use — that's the point of the isolation). Services talk to each
other over plain HTTP, the same way they would across containers or hosts.

| Service | Port | Responsibility |
|---|---|---|
| `gateway-service` | 5000 | Single entry point. Proxies `/api/<resource>/...` to the right backend service. |
| `auth-service` | 5001 | Registration, login, JWT issuing. Calls user-service to create a default profile. |
| `user-service` | 5002 | Profile storage. |
| `task-service` | 5003 | Task CRUD. Calls notification-service when a task gets a due date. Exposes an internal endpoint for analytics-service. |
| `category-service` | 5004 | Task categories/tags. |
| `notification-service` | 5005 | Stores and serves reminders/notifications. |
| `analytics-service` | 5006 | Calls task-service internally and computes completion stats on demand. |
| `health-service` | 5007 | Pings every service's `/health` endpoint and reports status + latency. Powers the frontend's status page. |

## Run it — no Docker

Requires Python 3.10+.

```bash
cd taskflow
./run_local.sh
```

This starts all 8 services plus a static server for the frontend on port 8080.
Open **http://localhost:8080** in your browser, create an account, and go.

Stop everything with:

```bash
./stop_local.sh
```

Logs for each service land in `logs/<service-name>.log` if something looks off.

## Run it — Docker

```bash
cd taskflow
docker compose up --build
```

Same ports as above: frontend on `:8080`, gateway on `:5000`.

## Using the app

1. **Sign up** on the landing page (calls `auth-service`, which calls
   `user-service` to create your profile).
2. **Tasks page** — add categories, add tasks, optionally set a due date. A due
   date triggers a call from `task-service` to `notification-service`, and
   you'll see the reminder appear in the Notifications panel.
3. **Analytics page** — `analytics-service` calls `task-service` on the fly and
   returns your completion rate and status breakdown. Nothing is cached.
4. **Service status page** — `health-service` checks every service's `/health`
   endpoint every 5 seconds and reports whether it's up, degraded, or down,
   along with response latency. Stop one service (e.g. `kill` its process or
   `docker compose stop analytics-service`) and watch this page pick it up.

## Notes on the design

- **Auth**: JWTs are signed with a shared `JWT_SECRET` env var. Each service
  that needs to verify a token carries its own small copy of the JWT helper
  (`auth_utils.py`) rather than importing a shared package — deliberately,
  since in a real deployment these services ship and version independently.
- **Storage**: everything is in-memory Python dicts for simplicity, so data
  resets when a service restarts. Swapping in SQLite or Postgres per service
  is a drop-in change and doesn't affect any other service.
- **Service-to-service calls** are plain synchronous HTTP with short timeouts
  and best-effort error handling (e.g. registration still succeeds even if
  user-service is briefly down) — a simplified stand-in for what you'd do
  with a message queue in a production system.
