# MinaSäljare

Sales  tracking app for a single youth team (guardians + coach), with support for multiple campaigns and yearly statistics.

## Backend (Django + DRF) – Local setup (SQLite)

Prereqs:
- Python 3.11+ recommended

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
python manage.py migrate
python manage.py runserver
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health/
```

## Backend – Development with PostgreSQL (Docker)

From repo root:

```bash
cp backend/.env.example backend/.env
docker compose -f backend/docker-compose.dev.yml --env-file backend/.env up -d

# run migrations against Postgres
POSTGRES_DB=minasaljare POSTGRES_USER=minasaljare POSTGRES_PASSWORD=minasaljare POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
	./.venv/bin/python backend/manage.py migrate
```

## Raspberry Pi deployment (Docker + Cloudflare Tunnel)

This project supports a per-project isolated stack (db + backend + reverse-proxy + cloudflared).

On the Pi:

```bash
cp .env.example .env
docker compose --env-file .env up -d --build
```

In Cloudflare (Tunnel dashboard), configure the tunnel/public hostname to route to `http://nginx:80`.

The reverse proxy is Nginx and routes `/api/` to the Django backend.

## Notes

- Secrets/config should be provided via environment variables for non-local environments.
- See [docs/specification.md](docs/specification.md) for the full functional spec.

## Git workflow (stage/main)

- Long-lived branches: `stage` and `main`
- All development happens in short-lived branches:
	- `feature/...`, `bugfix/...`, `hotfix/...`
- Merge flow:
	- `feature|bugfix|hotfix/*` → `stage`
	- `stage` → `main`
- GitLab CI:
	- Merge requests must pass pipelines
	- MRs to `stage` are only allowed from `feature|bugfix|hotfix/*`
	- MRs to `main` are only allowed from `stage`
