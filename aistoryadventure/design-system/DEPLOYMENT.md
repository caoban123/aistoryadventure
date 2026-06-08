# Deployment Guide

This project uses a static frontend plus FastAPI backend. Do not migrate to React, Tailwind, Next.js, or a build step for deployment.

## Deployment Stack

This repo deploys via **Cloudflare Tunnel + Coolify** on a local machine running 24/7. No VPS rental, no Caddy, no open inbound ports required.

- **Coolify** manages Docker containers for the FastAPI backend and static frontend.
- **Cloudflare Tunnel** (`cloudflared`) exposes services to the internet with automatic HTTPS and DNS.
- TLS termination happens at the Cloudflare edge — no local cert management needed.

### Tunnel → Service mapping

| Public URL | Coolify container | Port |
|---|---|---|
| `yourdomain.com` | frontend (player) | e.g. 3000 |
| `admin.yourdomain.com` | frontend (admin) or same container | e.g. 3000 |
| `api.yourdomain.com` | backend (FastAPI) | 8000 |

### Coolify setup

- Use `deploy/coolify/backend.Dockerfile` for the FastAPI API service.
- Use `deploy/coolify/frontend.Dockerfile` for the static player/admin frontend.
- Optionally use `deploy/coolify/docker-compose.yml` for one Docker Compose application.
- Set environment variables in Coolify's UI — never commit real `.env` or Firebase admin JSON.

### Cloudflare Tunnel setup

1. Install `cloudflared` on the local machine.
2. Authenticate: `cloudflared tunnel login`
3. Create tunnel: `cloudflared tunnel create ai-story`
4. Configure `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: yourdomain.com
    service: http://localhost:3000
  - hostname: admin.yourdomain.com
    service: http://localhost:3000
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

5. Add DNS routes:

```
cloudflared tunnel route dns ai-story yourdomain.com
cloudflared tunnel route dns ai-story admin.yourdomain.com
cloudflared tunnel route dns ai-story api.yourdomain.com
```

6. Run as a system service: `cloudflared service install`

## Production Shape

- Player app: `https://yourdomain.com`
- Admin app: `https://admin.yourdomain.com`
- Backend API: `https://api.yourdomain.com`

The player and admin frontends both read `frontend/config.js` at runtime. In production, copy `deploy/frontend/config.production.js.example` to the deployed `frontend/config.js` and set:

```js
window.AI_STORY_CONFIG = {
  API_BASE: "https://api.yourdomain.com",
};
```

## Backend Environment

Use `.env.production.example` as the template. Fill real values only on the machine running Coolify.

Required production checks:

- `APP_ENV=production`
- Set `STRICT_STARTUP_CHECKS=true` only after `/status` readiness is clean.
- `CORS_ORIGINS` includes only the tunnel-exposed player and admin origins (e.g. `https://yourdomain.com,https://admin.yourdomain.com`).
- `USE_LOCAL_STORE_IF_FIREBASE_MISSING=false`
- Firebase Admin SDK credentials set (e.g. `/etc/ai-story/firebase-admin.json`), mounted as a volume in Coolify.
- Provider API keys set in Coolify environment variables, never in frontend files.
- `LOCAL_DATA_DIR` and `CHROMA_PERSIST_DIR` point to a persistent volume outside the container so data survives restarts.

## Firebase Setup

In Firebase Console, add authorized domains:

- `yourdomain.com`
- `admin.yourdomain.com`

Set the first admin claim:

```
python scripts/set_admin_claim.py --email caoban170106@gmail.com
```

After setting a claim, sign out and sign in again so Firebase issues a fresh ID token.

## Local Smoke Test

Backend:

```
python -m uvicorn app.main:app --reload
```

Frontend:

```
cd frontend
python -m http.server 5500
```

Open:

- Player: `http://localhost:5500`
- Admin: `http://localhost:5500/admin.html`

## Production Service Templates

All deployment templates live in `deploy/coolify/`:

- `deploy/coolify/README.md` — step-by-step Coolify setup guide.
- `deploy/coolify/backend.Dockerfile` — builds the FastAPI API service.
- `deploy/coolify/frontend.Dockerfile` — serves the static player/admin frontend.
- `deploy/coolify/docker-compose.yml` — optional one-resource Coolify Docker Compose deployment.
- `deploy/frontend/config.production.js.example` — runtime `API_BASE` config template for production.

The `deploy/caddy/` and `deploy/systemd/` folders are kept for reference but are **not used** in this deployment — Cloudflare Tunnel replaces Caddy and the tunnel runs as a system service instead of a custom systemd unit.

## Pre-Launch Checklist

- `node --check frontend/app.js`
- `node --check frontend/admin.js`
- `python -m compileall app scripts`
- Cloudflare Tunnel is running: `cloudflared tunnel info`
- All three tunnel routes active and showing **Healthy** in the Cloudflare dashboard.
- `https://api.yourdomain.com/status` responds without exposing secrets.
- Player login works on `https://yourdomain.com`.
- Admin login works on `https://admin.yourdomain.com`.
- Firebase Authorized Domains includes both tunnel domains.
- `CORS_ORIGINS` in backend `.env` matches the tunnel domains exactly.
- Coolify persistent volumes configured for `data/` and `chroma_db/`.
- `/status` readiness is `ok` before public beta.
- Admin Readiness panel is `ok`.
- Maintenance, ban, points, rate limits, usage logging, History save/rename/export all work with real accounts.
- Create a backup: `python scripts/backup_local.py`
- Test restore once using `BACKUP_RESTORE.md`.
- Trust & Safety page is reachable from Login.
- Backups and restore steps are documented before inviting public users.