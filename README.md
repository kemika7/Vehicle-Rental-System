# Vehicle Rental System

Office vehicle rental management system. Employees can browse and rent vehicles from their office's fleet; admins manage vehicles, employees, and offices.

The repo ships two backend implementations against the same domain model:

- **FastAPI backend** (root) — primary, production-targeted, deployed via Docker Compose behind Nginx.
- **Django backend** (`django_backend/`) — alternative implementation using DRF + SimpleJWT.

A React + TypeScript + Vite SPA in `frontend/` consumes the API.

## Stack

| Layer       | Tech                                                              |
| ----------- | ----------------------------------------------------------------- |
| API (main)  | FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2.9, python-jose, bcrypt  |
| API (alt)   | Django 5.1, DRF 3.15, SimpleJWT, django-filter                    |
| Database    | PostgreSQL 16 (prod), SQLite (local/dev)                          |
| Frontend    | React 18, React Router 6, Axios, Vite 6, TypeScript 5             |
| Infra       | Docker (multi-stage), Docker Compose, Nginx 1.27 reverse proxy    |
| Tests       | pytest                                                            |

## Project layout

```
.
├── main.py                 # FastAPI entry point
├── database.py             # SQLAlchemy engine/session
├── models/                 # SQLAlchemy ORM models (employee, vehicle, office, rental)
├── schemas/                # Pydantic request/response schemas
├── routers/                # FastAPI routes (auth, health, vehicle, rental)
├── services/               # Business logic
├── core/                   # Config, dependencies, JWT/security
├── exceptions.py           # Domain exceptions
├── tests/                  # pytest suite
├── agent/                  # Standalone helper agent
├── django_backend/         # Parallel Django + DRF implementation
├── frontend/               # React + Vite SPA
├── nginx/                  # Reverse proxy config
├── Dockerfile              # Multi-stage image for the FastAPI app
└── docker-compose.yml      # db + app + nginx
```

## Domain model

- **Office** — location grouping employees and vehicles.
- **Employee** — user with role `admin` or `employee`; bcrypt-hashed password; belongs to an office.
- **Vehicle** — has `type` (sedan, suv, van, truck, hatchback) and `status` (available, rented, maintenance); belongs to an office.
- **Rental** — links an employee to a vehicle with `status` (active, completed, cancelled).

## Running locally

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# generate JWT secret
openssl rand -hex 32   # paste into JWT_SECRET_KEY in .env

docker compose up --build
```

- API available through Nginx at `http://localhost:${NGINX_PORT:-80}`
- The `app` service is not exposed directly; Nginx is the only public entry point.
- Postgres data persists in the `postgres_data` named volume.

### Option B — FastAPI directly

```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

export JWT_SECRET_KEY=$(openssl rand -hex 32)
# DATABASE_URL is optional; defaults to local SQLite (vehicle_rental.db)

uvicorn main:app --reload
```

Interactive docs: `http://localhost:8000/docs`

### Option C — Django backend

```bash
cd django_backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # Vite dev server on http://localhost:5173
npm run build        # production build to dist/
```

The frontend expects the API origin to be allowed via `CORS_ORIGINS` on the backend (defaults already include `http://localhost:5173`).

## Configuration

Environment variables (see `.env.example`):

| Variable                              | Purpose                                          |
| ------------------------------------- | ------------------------------------------------ |
| `POSTGRES_USER` / `_PASSWORD` / `_DB` | Postgres credentials (compose only)              |
| `DATABASE_URL`                        | SQLAlchemy URL; falls back to local SQLite       |
| `JWT_SECRET_KEY`                      | **Required.** 32-byte hex secret for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES`         | Token lifetime (default 60)                      |
| `CORS_ORIGINS`                        | Comma-separated allowed origins                  |
| `NGINX_PORT`                          | Public port for the reverse proxy                |

## Authentication

- `POST /auth/register` — create an employee account.
- `POST /auth/login` — exchange credentials for a JWT bearer token.
- Pass the token as `Authorization: Bearer <token>` on protected routes.
- Admin-only endpoints are guarded by role checks in `core/dependencies.py`.

## Tests

```bash
pytest
```

Configuration lives in `pytest.ini`; the suite is in `tests/`.

## Docker image notes

`Dockerfile` is a two-stage build:

1. Builder stage installs deps into `/root/.local`.
2. Runtime stage is `python:3.12-slim`, copies only the installed packages, runs as a non-root `app` user, and exposes port 8000.

A stdlib-based `HEALTHCHECK` hits `/health` — no `curl` required in the image.
