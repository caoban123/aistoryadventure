# Deployment Guide

This project stays as a static frontend plus FastAPI backend. Do not migrate to React, Tailwind, Next.js, or a build step for deployment.

## VPS Deployment Pack v2

Copy-ready templates live in `deploy/`:

- `deploy/coolify/README.md`
- `deploy/coolify/docker-compose.yml`
- `deploy/coolify/backend.Dockerfile`
- `deploy/coolify/frontend.Dockerfile`
- `deploy/caddy/Caddyfile.example`
- `deploy/systemd/ai-story-api.service.example`
- `deploy/systemd/ai-story-backup.service.example`
- `deploy/systemd/ai-story-backup.timer.example`
- `deploy/frontend/config.production.js.example`
- `deploy/README.md`

Use `deploy/coolify/README.md` if deploying with Coolify. Use `deploy/README.md` for the manual Caddy + systemd path.

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

Use `.env.production.example` as the template for the VPS environment. Fill the real values only on the server.

Required production checks:

- `APP_ENV=production`.
- Set `STRICT_STARTUP_CHECKS=true` only after `/status` readiness is clean.
- `CORS_ORIGINS` includes only the player and admin origins.
- `USE_LOCAL_STORE_IF_FIREBASE_MISSING=false`.
- Firebase Admin SDK credentials live outside the repo, for example `/etc/ai-story/firebase-admin.json`.
- Provider API keys live only in server env/secrets, never in frontend files.
- Persistent paths such as `LOCAL_DATA_DIR` and `CHROMA_PERSIST_DIR` point outside the repo.

## Firebase Setup

In Firebase Console, add authorized domains for:

- `yourdomain.com`
- `admin.yourdomain.com`

Admin permissions still come from the backend-verified Firebase custom claim:

```powershell
venv\Scripts\python.exe scripts\set_admin_claim.py --email caoban170106@gmail.com
```

After setting a claim, sign out and sign in again so Firebase issues a fresh ID token.

## Local Smoke Test

Backend:

```powershell
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
python -m http.server 5500
```

Open:

- Player: `http://localhost:5500`
- Admin: `http://localhost:5500/admin.html`

## Production Service Templates

Coolify path:

- use `deploy/coolify/backend.Dockerfile` for the FastAPI API service
- use `deploy/coolify/frontend.Dockerfile` for the static player/admin frontend
- optionally use `deploy/coolify/docker-compose.yml` for one Docker Compose application
- use Coolify domains/SSL instead of installing Caddy manually

Manual VPS path:

Use the files in `deploy/caddy/` and `deploy/systemd/` instead of copying snippets from this document. They include:

- static player/admin serving
- API reverse proxy
- `config.js` no-store cache header
- managed FastAPI restart
- daily local runtime backup timer

## Pre-Launch Checklist

- `node --check frontend/app.js`
- `node --check frontend/admin.js`
- `venv\Scripts\python.exe -m compileall app scripts`
- Create a backup with `venv\Scripts\python.exe scripts\backup_local.py`.
- Test restore once in a non-production copy using `BACKUP_RESTORE.md`.
- Player login works on the production domain.
- Admin login works on the admin subdomain.
- `/status` responds without exposing secrets.
- `/status` stays responsive even if live Firestore settings are slow.
- Admin Readiness panel is `ok` before public beta.
- Trust & Safety page is reachable from Login.
- Maintenance, ban, points, rate limits, usage logging, History save/rename/export all work with real accounts.
- Backups and restore steps are documented before inviting public users.
