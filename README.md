# AI Story Adventure

AI Story Adventure is a cinematic AI storytelling app with Adventure, Novel, History, Firebase auth, admin controls, usage/rate limits, and ChromaDB memory.

## Quick Start

Backend:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
source venv/bin/activate
```

Frontend:

```bash
cd frontend
python -m http.server 5500
```
uvicorn app.main:app --reload --port 8002 --host 0.0.0.0
python3 -m http.server 5500
Open:

- Player: `http://localhost:5500`
- Admin: `http://localhost:5500/admin.html`

The frontend reads `frontend/config.js` for the backend URL. Local default:

```js
API_BASE: "http://127.0.0.1:8000"
```

## API

- `POST /game/start`
- `POST /game/turn`
- `GET /game/{session_id}`
- `GET /game/sessions`
- `GET /game/worlds`
- `GET /status`
- `GET /admin/me`

## Configuration Notes

For local testing before configuring Firebase/API keys:

```env
TEXT_PROVIDER=mock
USE_LOCAL_STORE_IF_FIREBASE_MISSING=true
```

OpenAI:

```env
TEXT_PROVIDER=openai
TEXT_MODEL=gpt-4o-mini
OPENAI_API_KEY=...
```

Gemini:

```env
TEXT_PROVIDER=gemini
TEXT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=...
```

Ollama:

```env
TEXT_PROVIDER=ollama
TEXT_MODEL=llama3:latest
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

Firebase uses `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_SERVICE_ACCOUNT_JSON`.

## Production

Use:

- `.env.production.example` for backend environment shape.
- `deploy/frontend/config.production.js.example` for production API base.
- `DEPLOYMENT.md` for VPS/domain/Caddy notes.
- `deploy/README.md` for the copy-ready VPS deployment pack.
- `BACKUP_RESTORE.md` for local runtime backup and restore steps.

Never commit real `.env`, Firebase admin JSON, or provider API keys.

Before public beta, check `/status` and the admin Readiness panel. Production should use `APP_ENV=production` and should reach readiness `ok`.
