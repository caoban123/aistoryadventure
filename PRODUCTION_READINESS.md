# Production Readiness Roadmap

This file is the source of truth for preparing AI Story Adventure for real public users, a custom domain, and VPS deployment.

## Non-Negotiable Rules

- Do not make an admin page that is protected only by hidden frontend buttons.
- Admin permission must be enforced by the backend using verified Firebase auth and an admin role/claim.
- Do not expose `.env`, Firebase admin JSON, API keys, provider tokens, admin tokens, or full secret paths in any frontend response.
- Do not change existing game API contracts casually. Production work should wrap or extend safely.
- Do not mock users, sessions, AI usage, or admin stats in production flows.
- Every destructive admin action needs confirmation and an audit log entry.

## Recommended Build Order

### 1. Admin Role Foundation

Goal: define who is allowed to use admin tools.

Required:

- Add a real admin role strategy.
- Prefer Firebase custom claims such as `admin: true`, set only from a privileged backend/admin environment.
- Add backend helper/middleware that verifies Firebase ID token and rejects non-admin users.
- Add a simple admin-only endpoint such as `GET /admin/me` to confirm role and permissions.

Notes:

- Frontend role checks are only for UI convenience.
- Backend must always be the source of truth.
- Do not put admin emails directly in frontend code.
- First admin email for this repo: `caoban170106@gmail.com`.
- Set the first admin claim from the backend environment with:

```powershell
venv\Scripts\python.exe scripts\set_admin_claim.py --email caoban170106@gmail.com
```

- After setting the claim, sign out and sign in again so Firebase issues a fresh ID token.

### 2. Admin Backend API v1

Goal: create real admin data endpoints before building a big dashboard.

Start with read-heavy, low-risk endpoints:

- `GET /admin/overview`: user/session/story counts, provider status, catalog count.
- `GET /admin/sessions`: recent sessions with filters.
- `GET /admin/users`: basic user list or known user identities if available.
- `GET /admin/errors`: recent backend/provider errors if logging exists.
- `GET /admin/usage`: estimated AI usage and high-demand/failure counts.
- Current admin control endpoints also include settings, points, ban/unban, ledger, and audit:
  - `GET/PATCH /admin/settings`
  - `POST /admin/users/{uid}/points`
  - `POST /admin/users/{uid}/ban`
  - `POST /admin/users/{uid}/unban`
  - `GET /admin/points/ledger`
  - `GET /admin/audit`

Add write actions only after audit logging exists:

- Delete abusive/broken sessions.
- Disable or flag abusive users.
- Refresh/rebuild catalog data if needed.

Notes:

- Paginate lists from the start.
- Never return full secrets or raw credentials.
- Return only fields needed by the admin UI.

### 3. Admin Dashboard v1

Goal: build a practical admin page after backend guards exist.

Current implementation note:

- Admin is separated from the player frontend as `frontend/admin.html`, with its own `frontend/admin.js` and `frontend/admin.css`.
- Local admin URL: `http://localhost:5500/admin.html`.
- Production should map an admin subdomain such as `admin.yourdomain.com` to this admin shell.
- The player app must not include an embedded `adminPage` or an `Admin Console` avatar dropdown shortcut.
- Firebase Authorized Domains and backend `CORS_ORIGINS` must include both the player domain and the admin subdomain.
- Admin v2 tracks safe AI usage metadata, daily rate limits, points, maintenance, ban/unban, sessions previews, and audit logs. It does not expose full conversations or web-editable API keys.
- Admin uses a separate Firebase app name and session persistence so local `admin.html` login does not sign the player frontend into the same account.
- Player login calls `GET /account/status` after Firebase auth; maintenance and ban notices stay on the login screen instead of sending blocked users into the app.

Recommended panels:

- System health: backend online, provider/model, storage mode, catalog count.
- Usage: sessions today, turns today, Novel/Adventure split, AI error/high-demand count.
- Users: recent users, session count, last activity, basic status.
- Sessions: recent sessions, mode, saved/draft, updated time, safe preview.
- Errors: recent API/provider errors.
- Admin audit: recent admin actions.

UI rules:

- Keep static HTML/CSS/JS architecture.
- Match cinematic fantasy/admin console style, but prioritize dense readable data.
- No fake rows or mock stats.
- Empty/error/loading states are required.
- Destructive buttons must be visually distinct and confirmed.

### 4. Rate Limit + Cost Control

Goal: prevent AI abuse before public launch.

Required:

- Per-user turn limit.
- Per-user story creation limit.
- Maximum `target_words`.
- Cooldown/backoff for repeated high-demand/provider errors.
- Optional guest restrictions if guest mode remains enabled.

Recommended:

- Track AI requests by user/session/day.
- Add admin overview for usage spikes.
- Add graceful user-facing messages when limits are reached.

Notes:

- This protects both cost and service stability.
- Do not rely on frontend disabling alone.

### 5. Logging, Monitoring, Audit Trail

Goal: know what happened when something breaks.

Log categories:

- API errors.
- AI provider errors/high demand/rate limit.
- Auth failures.
- Session create/save/delete/turn.
- Admin actions.
- Startup/deployment config summary without secrets.

Monitoring basics:

- Backend alive check.
- CPU/RAM/disk on VPS.
- Error rate.
- AI provider failure rate.
- Storage/ChromaDB availability.

Notes:

- Separate security/audit logs from normal debug noise where possible.
- Logs must not include API keys, Firebase credentials, or full user private content unless explicitly needed and protected.

### 6. Backup + Restore

Goal: avoid losing real users' stories.

Back up:

- Firebase/Firestore data or any production datastore.
- `chroma_db` or vector memory storage.
- Catalog data if it becomes editable.
- Production config templates, excluding secrets.

Required before public launch:

- Document restore steps.
- Test restore once on a non-production copy.
- Decide backup frequency.

Notes:

- A backup that was never restored is only a hope, not a recovery plan.
- Current repo support: `scripts/backup_local.py`, `scripts/restore_local.py`, and `BACKUP_RESTORE.md`.
- Local runtime backups include `data/` and `chroma_db/`; they intentionally exclude `.env`, Firebase admin JSON, provider keys, `venv`, and `node_modules`.
- Firestore production data still needs Firebase/GCP export in addition to local runtime backup.

### 7. Production Configuration + Secrets

Goal: make local/dev and production configs explicit.

Required:

- Separate dev/prod `.env` values.
- Set `APP_ENV=production` for the public backend.
- Lock CORS to the real domain in production.
- Store Firebase admin credentials safely.
- Rotate any keys that were accidentally committed or shared.
- Add clear startup checks for required production env vars.

Notes:

- Never commit real `.env` or Firebase admin JSON.
- Frontend Firebase config can be public, but admin service credentials cannot.
- The static frontend reads `frontend/config.js` at runtime for `API_BASE`; production should deploy a server-specific `config.js` based on `deploy/frontend/config.production.js.example`.
- Use `.env.production.example` as a server-only production template and keep real values on the VPS, not in the repository.
- See `DEPLOYMENT.md` for the local smoke test, Caddy example, and domain/subdomain checklist.
- Current backend exposes safe readiness metadata through `/status` and admin overview.
- Public `/status` stays non-blocking and may skip live Firestore app settings; use the admin Readiness panel for the final production-ready decision.
- `STRICT_STARTUP_CHECKS=true` can be enabled after the admin Readiness report is clean.

### 8. VPS + Domain Deployment

Goal: serve the app safely and reliably.

Recommended stack:

- Domain DNS points to VPS.
- Reverse proxy such as Caddy or Nginx handles HTTPS.
- FastAPI runs behind the proxy with Uvicorn/Gunicorn/systemd or Docker.
- Static frontend served by reverse proxy or a simple static host path.
- Backend runs as a managed service with auto restart.

Required production checks:

- HTTPS works.
- API base points to production backend.
- CORS accepts only intended domains.
- Firebase authorized domains include the production domain.
- Backend restarts after reboot.
- Logs are accessible.

Current repo support:

- `deploy/coolify/README.md` contains the recommended Coolify deployment path.
- `deploy/coolify/backend.Dockerfile` and `deploy/coolify/frontend.Dockerfile` deploy the API and static player/admin frontend with no React/Tailwind/build-system migration.
- `deploy/coolify/docker-compose.yml` is available for a one-resource Coolify Docker Compose deployment.
- `deploy/README.md` contains the VPS checklist.
- `deploy/caddy/Caddyfile.example` serves player/admin static files and proxies API.
- `deploy/systemd/ai-story-api.service.example` runs the FastAPI backend.
- `deploy/systemd/ai-story-backup.service.example` and `.timer.example` schedule local runtime backups.

### 9. Public-Facing Legal + Trust Pages

Goal: make the app safer for real users.

Minimum:

- Privacy Policy.
- Terms of Service.
- Contact/support email.
- AI-generated content notice.
- Data deletion/contact process.

Notes:

- This matters once strangers can create accounts and save story data.
- Current repo support: player frontend includes a bilingual `Trust & Safety` page from Login with Privacy, Terms, AI Content Notice, and Contact/Data Deletion guidance.

### 10. Public Beta Launch

Goal: launch to a small group first.

Before beta:

- Admin role works.
- Admin dashboard v1 works.
- Rate limits are active.
- Backup/restore is documented.
- HTTPS/domain works.
- Error and usage logs are visible.
- Real user flows tested: sign in, create, save to History, continue, submit turn, logout.

After beta starts:

- Watch AI usage daily.
- Watch error logs daily.
- Review abusive/spam behavior.
- Collect UI/flow feedback.
- Fix production issues before adding large new features.

## References

- Firebase custom claims: https://firebase.google.com/docs/auth/admin/custom-claims
- FastAPI deployment concepts: https://fastapi.tiangolo.com/deployment/concepts/
- FastAPI HTTPS/proxy notes: https://fastapi.tiangolo.com/deployment/https/
- OWASP API Security Top 10: https://owasp.org/API-Security/
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
