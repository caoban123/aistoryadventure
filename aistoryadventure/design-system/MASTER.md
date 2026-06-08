# AI Story Adventure Design System

This document adapts UI/UX Pro Max-style design discipline to this project. It is a project-specific design system, not a framework migration plan.

## Product Identity

AI Story Adventure is a cinematic fantasy storytelling app. The interface should feel like a portal into a living archive of adventures, not like a generic SaaS dashboard.

Core mood:

- Cinematic fantasy
- Cosmic depth
- Portal archive
- Dark glass panels
- Warm gold accents
- Readable story-first layouts

Avoid:

- Generic SaaS hero sections
- Bright neon palettes
- One-note purple gradients
- Decorative clutter that competes with story text
- Mock/demo content in real user flows

## Architecture Constraints

- Frontend stays static: HTML, CSS, and vanilla JavaScript.
- Do not introduce React, Tailwind, Next.js, Vite, or a build step.
- Use the existing files unless the user asks for a new structure:
  - `frontend/index.html`
  - `frontend/style.css`
  - `frontend/app.js`
- Backend API contracts stay stable. Frontend changes must adapt to existing backend responses.
- Real flows must keep using real endpoints:
  - `/game/start`
  - `/game/turn`
  - `/game/novel/world`
  - `/game/novel/foundation`
  - `/game/sessions`
  - `/game/{session_id}`

## Visual System

- Use the existing dark cosmic base with glass panels and gold highlights.
- Keep typography aligned with the current Cinzel/Lora/JetBrains Mono direction.
- Use restrained motion: portal motion, reveal, and loading animations should support orientation and state, not distract.
- Cards should be individual items, modals, or tool surfaces. Do not nest cards inside cards.
- Use stable dimensions for toolbars, buttons, cards, grids, composer, and fixed controls.
- Text must wrap cleanly on mobile. Never allow long names, emails, IDs, titles, or story summaries to break layout.

## Interaction Rules

- All clickable controls must be native buttons/links or have equivalent keyboard behavior.
- Async actions need visible states: idle, loading, retrying, cancelled, success, and error.
- AI-heavy flows use resilient loading with Cancel:
  - Adventure start
  - Novel world creation
  - Novel foundation creation
  - Game turn submit
- Do not retry validation/auth/permission errors indefinitely.
- Firebase clock/token errors should explain how to sync the device clock; the browser must not try to set system time.

## Accessibility Rules

- Keep contrast readable against dark glass backgrounds.
- Use visible labels for forms and helper/error text near fields.
- Add `aria-live` to async status areas.
- Modals need a clear cancel/close action.
- Respect `prefers-reduced-motion`.
- Preserve browser zoom and avoid horizontal scrolling on mobile.
- Maintain touch targets around 44px or larger for primary controls.

## Page Patterns

- Home and Discover: cinematic catalog browsing with real world data only.
- History: saved-story archive, not draft storage. Empty states must clarify that only manually saved stories appear.
- Foundation: readable world/profile summary with a clear begin/save path.
- Game: reading studio first, composer second, choices clear and touch-friendly.
- Profile: account dossier from Firebase user data only.
- Loading: compact resilient panel for AI flows, separate from auth login loading.

## Pre-Delivery Checklist

Before finishing UI work:

- `node --check frontend/app.js` passes when JavaScript changes.
- Desktop layout has no overlap.
- Mobile layout has no horizontal scroll or clipped buttons.
- Reduced-motion mode is usable.
- Loading, empty, error, disabled, and success states are present where relevant.
- Backend calls remain real; no mock sessions, mock stories, fake choices, or fake profile data.
