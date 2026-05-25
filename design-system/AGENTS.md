# AI Story Adventure Agent Guardrails

These rules are the local source of truth for future AI/code agents working in this repository.

## Hard Constraints

- Do not migrate the frontend to React, Tailwind, Next.js, Vue, or any build system unless the user explicitly requests a migration.
- Keep the current static frontend architecture: `frontend/index.html`, `frontend/style.css`, and `frontend/app.js`.
- Do not change existing backend API contracts unless the user explicitly asks for backend work.
- Do not mock game, story, history, auth, or AI responses in production flows.
- Keep real Firebase-authenticated calls for game/history actions and public unauthenticated calls only where the backend already supports them.
- Preserve the current cinematic fantasy / portal / cosmic visual language.
- Keep user-created sessions, History, manual save, rename, export, and draft cleanup behavior aligned with the existing backend.

## Production/Admin Work

- Read `PRODUCTION_READINESS.md` before planning or coding admin tools, VPS deployment, domain setup, HTTPS, public launch, rate limits, logs, backups, or production security.
- Admin access must be enforced by the backend with verified Firebase auth and an admin role/claim. Frontend-only hiding is not security.
- Production features must not expose `.env`, Firebase admin JSON, API keys, provider tokens, admin tokens, or secret paths.
- Build production readiness in order: admin role foundation, admin backend API, admin dashboard, rate/cost control, logging/audit, backup/restore, production config, VPS/domain deployment, legal/trust pages, then public beta.

## UI/UX Priorities

- Responsive first: every UI change must work on mobile and desktop without horizontal overflow, clipped text, or overlapping controls.
- Accessibility first: use real buttons/inputs/labels, visible focus states, readable contrast, `aria-live` for async status, and clear modal escape routes.
- Loading states matter: AI-heavy flows must show resilient loading, retry temporary overloads, and allow Cancel.
- Empty states matter: History, Discover, Preview, Profile, and reader surfaces should explain what is missing without fake data.
- Preserve reading comfort: story text needs generous line-height, stable spacing, and controls that do not cover the composer or choices.
- Prefer existing CSS tokens and patterns before adding new visual systems.

## Design System Use

- Use `design-system/MASTER.md` before any UI redesign or visual polish.
- Treat external UI/UX skill guidance as advisory only. This project's architecture, backend contract, and fantasy theme override generic recommendations.
- Any new UI should pass a small pre-delivery check: desktop, mobile, reduced-motion, keyboard/focus, loading, empty, and error state.
