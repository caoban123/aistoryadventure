# VPS Deployment Pack v2

This folder contains copy-ready templates for deploying AI Story Adventure on a Linux VPS.

Recommended for first production deploy:

- Coolify: use `coolify/README.md`

Manual fallback:

- Caddy + systemd: use this document and the `caddy/` / `systemd/` templates

## Files

- `coolify/README.md`: step-by-step Coolify guide.
- `coolify/docker-compose.yml`: optional one-resource Docker Compose deployment.
- `coolify/backend.Dockerfile`: FastAPI backend image.
- `coolify/frontend.Dockerfile`: static player/admin frontend image.
- `coolify/frontend.nginx.conf`: nginx routing for player and admin subdomain.
- `caddy/Caddyfile.example`: HTTPS reverse proxy and static frontend serving.
- `systemd/ai-story-api.service.example`: FastAPI managed service.
- `systemd/ai-story-backup.service.example`: one-shot local runtime backup.
- `systemd/ai-story-backup.timer.example`: daily backup timer.
- `frontend/config.production.js.example`: production runtime frontend config.

## Coolify Quick Start

1. Install Coolify on the VPS.
2. Create DNS records for `aistoryadventure.xyz`, `api.aistoryadventure.xyz`, `admin.aistoryadventure.xyz`, and `panel.aistoryadventure.xyz`.
3. Deploy the backend with `coolify/backend.Dockerfile`, domain `https://api.aistoryadventure.xyz`, port `8000`, and persistent storage `/data/ai-story`.
4. Deploy the frontend with `coolify/frontend.Dockerfile`, domains `https://aistoryadventure.xyz` and `https://admin.aistoryadventure.xyz`, port `8080`.
5. Paste production environment variables from `coolify/coolify.env.example` into Coolify.
6. Validate `/status`, player login, admin login, save/history, points, rate limits, and maintenance mode.

See `coolify/README.md` before starting the VPS work.

## Target Layout

Use this layout on the VPS:

```text
/opt/ai-story/                 app code
/opt/ai-story/frontend/        static player/admin frontend
/opt/ai-story/venv/            Python virtualenv
/etc/ai-story/ai-story.env     production env, never committed
/etc/ai-story/firebase-admin.json
/var/lib/ai-story/data
/var/lib/ai-story/chroma_db
/var/backups/ai-story
```

## Domain Shape

- Player: `https://yourdomain.com`
- Admin: `https://admin.yourdomain.com`
- API: `https://api.yourdomain.com`

## First Deploy Checklist

1. Create DNS records:
   - `A yourdomain.com -> VPS_IP`
   - `A admin.yourdomain.com -> VPS_IP`
   - `A api.yourdomain.com -> VPS_IP`
2. Add Firebase Authorized Domains:
   - `yourdomain.com`
   - `admin.yourdomain.com`
3. Create the server user and folders:
   - user: `ai-story`
   - app path: `/opt/ai-story`
   - config path: `/etc/ai-story`
   - data path: `/var/lib/ai-story`
   - backup path: `/var/backups/ai-story`
4. Copy `.env.production.example` to `/etc/ai-story/ai-story.env` and fill real values.
5. Copy Firebase Admin SDK JSON to `/etc/ai-story/firebase-admin.json`.
6. Copy `deploy/frontend/config.production.js.example` to `/opt/ai-story/frontend/config.js` and set the real API domain.
7. Install Python 3.11+, create `/opt/ai-story/venv`, and install `requirements.txt`.
8. Copy the systemd examples into `/etc/systemd/system/` without `.example`.
9. Copy the Caddy example to `/etc/caddy/Caddyfile` and replace domains.
10. Start services:
    - `systemctl daemon-reload`
    - `systemctl enable --now ai-story-api.service`
    - `systemctl enable --now ai-story-backup.timer`
    - `systemctl reload caddy`

## Production Validation

Run these checks after deployment:

```bash
curl -s https://api.yourdomain.com/status
systemctl status ai-story-api.service
systemctl list-timers ai-story-backup.timer
journalctl -u ai-story-api.service -n 100 --no-pager
```

Then verify in the browser:

- Player login works.
- Admin login works and admin Readiness panel is clean.
- Create Adventure/Novel works with the real AI provider.
- Manual Save appears in History.
- Maintenance, ban, rate limit, and points controls work from admin.
- Backup timer creates files in `/var/backups/ai-story`.

## Safety Notes

- Do not copy `.env`, Firebase Admin SDK JSON, or provider keys into `frontend/`.
- Do not expose `/etc/ai-story` or `/var/lib/ai-story` through Caddy.
- Keep `STRICT_STARTUP_CHECKS=false` until admin Readiness is clean, then turn it on.
- Keep Firestore/GCP export as the source of truth for Firestore backups; local backup covers `data/` and `chroma_db/`.
