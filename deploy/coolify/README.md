# Coolify Deployment Pack

This pack deploys AI Story Adventure with Coolify while keeping the existing static frontend and FastAPI backend.

## Target Domains

```text
https://aistoryadventure.xyz        player app
https://admin.aistoryadventure.xyz  admin app
https://api.aistoryadventure.xyz    FastAPI backend
https://panel.aistoryadventure.xyz  Coolify panel
```

## DNS

Create these records before deploying:

```text
A  @      VPS_IP
A  api    VPS_IP
A  admin  VPS_IP
A  panel  VPS_IP
```

Use DNS-only while first validating SSL. After everything works, Cloudflare proxy can be enabled carefully.

## Option A: Recommended Separate Coolify Apps

Create two Coolify Applications from the same Git repository.

### Backend App

- Dockerfile: `deploy/coolify/backend.Dockerfile`
- Port: `8000`
- Domain: `https://api.aistoryadventure.xyz`
- Persistent storage mount: `/data/ai-story`
- Environment variables: paste values from `deploy/coolify/coolify.env.example`

Required secret values:

- `GEMINI_API_KEY`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_SERVICE_ACCOUNT_JSON`

For `FIREBASE_SERVICE_ACCOUNT_JSON`, paste the Firebase Admin SDK JSON as a locked runtime secret. Multiline or minified JSON both work because the backend reads it with `json.loads`.

### Frontend App

- Dockerfile: `deploy/coolify/frontend.Dockerfile`
- Port: `8080`
- Domains:

```text
https://aistoryadventure.xyz
https://admin.aistoryadventure.xyz
```

- Environment variable:

```text
API_BASE=https://api.aistoryadventure.xyz
```

The frontend container writes `frontend/config.js` at startup, so `config.js` is always tied to the production API. The nginx config serves `admin.html` automatically on the `admin.` subdomain and `index.html` everywhere else.

## Option B: Docker Compose App

Create one Coolify Docker Compose Application and point it at:

```text
deploy/coolify/docker-compose.yml
```

Set all variables from `deploy/coolify/coolify.env.example`.

Assign domains in Coolify:

- `api` service, port `8000`: `https://api.aistoryadventure.xyz`
- `web` service, port `8080`: `https://aistoryadventure.xyz,https://admin.aistoryadventure.xyz`

If Coolify asks for domains with explicit ports, use:

```text
https://api.aistoryadventure.xyz:8000
https://aistoryadventure.xyz:8080,https://admin.aistoryadventure.xyz:8080
```

## Firebase Setup

In Firebase Console, add authorized domains:

```text
aistoryadventure.xyz
admin.aistoryadventure.xyz
```

Admin access still requires the backend Firebase custom claim:

```powershell
venv\Scripts\python.exe scripts\set_admin_claim.py --email caoban170106@gmail.com
```

After setting the claim, sign out and sign in again.

## Validation

Open:

```text
https://api.aistoryadventure.xyz/status
https://aistoryadventure.xyz
https://admin.aistoryadventure.xyz
```

Then test:

- Player login
- Adventure or Novel creation
- Manual Save to History
- Continue from History
- Admin login
- Maintenance mode
- Ban/unban
- Points and rate limits

## Safety Notes

- Do not commit real `.env` values or Firebase Admin SDK JSON.
- `.dockerignore` excludes local secrets, runtime data, backups, `venv`, and `node_modules` from Docker builds.
- Keep `STRICT_STARTUP_CHECKS=false` for the first deploy. Turn it on only after `/status` and the admin Readiness panel are clean.
- Use Coolify persistent storage for `/data/ai-story`, otherwise local data and ChromaDB memory can disappear on redeploy.
