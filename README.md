# WhiteBalloon

**WhiteBalloon** is a socially-authenticated mutual aid network built on an **open, transparent social graph** where every connection and interaction is publicly inspectable but personally private. Identities are represented by **disposable private keys** that are socially cross-authenticated — your inviter cryptographically vouches for you, forming a chain of verified trust rather than a database of static profiles. The result is a decentralized web of relationships where authenticity is earned, not claimed.

At its core, WhiteBalloon is a **trust-driven coordination engine**: an invite-only network where every participant begins by expressing a real need and where visibility, recommendations, and introductions are shaped by degrees of separation. The **AI layer** continuously reads the open graph to suggest helpers, draft introductions, and surface mutual aid opportunities across clusters of trust. The infrastructure — built on FastAPI, SQLModel, and open cryptographic primitives — is deliberately minimal, designed to make social cooperation computationally legible without centralizing control. By merging open data, social verification, and AI mediation, WhiteBalloon reimagines the social network as an *infrastructure of care and reciprocity*, not performance.

# Technical Info

WhiteBalloon is a modular FastAPI + SQLModel application that ships with invite-only authentication and a lightweight help-request feed. The project serves as a foundation for layering additional atomic modules without adopting heavy frontend frameworks.

## Features
- Invite-based registration with automatic admin bootstrap for the first user
- Auto-approval for invite-based registrations (configurable per invite), allowing trusted users to land in a fully authenticated session immediately
- Multi-device login approvals powered by verification codes
- Session management via secure cookies backed by the database
- Help-request feed with progressive enhancement for creating and completing requests
- Admin-only profile directory ( `/admin/profiles` ) with per-account drill-downs to review contact info, sharing scope, requests, and invite history
- Admin control panel (`/admin`) that centralizes links to the directory, sync dashboard, and future operator tools
- Per-request detail pages with shareable URLs and consistent permissions
- Comment threads on request detail pages with progressive enhancement (vanilla JS) for instant posting
- Manual sync bundles (`*.sync.txt`) use email-style headers plus plain-text bodies so exports are Git-friendly
- Vanilla CSS design system with reusable layout primitives and components
- JSON API under `/api/requests` for programmatic access to the request feed
- Invite generation returns share-ready links using the current request origin (fallback to `SITE_URL`)
- Animated, bubbly theme with gradient background/responsive cards inspired by mutual-aid celebrations (respects `prefers-reduced-motion`)
- Admin-only Sync Control Center (`/admin/sync-control`) for managing peers, triggering push/pull jobs, and reviewing recent sync activity

## Typography

WhiteBalloon ships self-hosted variable fonts to keep typography distinctive without third-party requests:

- **Sora** (headings, accents) — SIL Open Font License
- **Inter** (body copy, UI) — SIL Open Font License

Both WOFF2 files live under `static/fonts/` and load via `@font-face` in `static/css/app.css`. When updating fonts, download the latest releases from the upstream projects, convert to WOFF2 if needed, and replace the existing files with the same filenames so the CSS continues to resolve them. Keep the font-weight axis between 400–700 to match the existing usage.

## Quick start

Requires Python 3.10+.

1. **Setup the environment** (creates venv, installs deps, initializes database)
   ```bash
   ./wb setup
   ```
   On Windows:
   ```cmd
   wb.bat setup
   ```

2. **Run the development server**
   ```bash
   ./wb runserver
   ```
   On Windows:
   ```cmd
   wb.bat runserver
   ```
   Visit `http://127.0.0.1:8000` to access the interface.

> **Note**: The first registered user (no invite token required) becomes an administrator automatically.

> **Database integrity**: Re-run `./wb init-db` whenever you suspect schema drift. The command now checks tables/columns against SQLModel definitions, auto-creates missing pieces, and reports mismatches that require manual attention.

> **Invite links**: By default invite links use the incoming request origin. Set `SITE_URL` in `.env` to provide a fallback host for CLI usage or non-HTTP contexts.
>
> **Sync Control Center**: After logging in as an administrator, open `/admin/sync-control` (also linked from `/sync/public`) to edit peers, run push/pull jobs, and monitor activity without leaving the browser.

## Manual sync bundles & signatures

Stage 5 of the sync plan introduces signed bundles so operators can trust data pulled from peers:

1. Generate a signing keypair once per instance:
   ```bash
   ./wb sync keygen
   ```
   The private key lives under `.sync/keys/` and the CLI prints the base64 public key you should share with peers. The key is auto-created the first time you run any sync command if it’s missing.
2. Register peers with their bundle directory and public key so pulls can authenticate signatures:
   ```bash
   ./wb sync peers add --name hub --path ../shared/public_sync --public-key <base64>
   ```
3. Export/push flows now sign `manifest.sync.txt`, emit `bundle.sig`, and drop your public key under `data/public_sync/public_keys/<key-id>.pub`. Multiple operators can share the same bundle directory; each signer writes/updates only their own file.
4. `./wb sync pull <peer>` and `./wb sync import <dir> --peer <name>` verify the signature before applying data. Use `--allow-unsigned` only when working with historical bundles that predate signatures.

### Bootstrap a new instance from a shared bundle (filesystem)

1. Clone the repo (or otherwise sync `data/public_sync/`) and run `./wb setup`.
2. Register the bundle + public key so imports can verify it:
   ```bash
   ./wb sync peers add --name origin --path data/public_sync --public-key <base64>
   ```
   The `<base64>` value lives in `data/public_sync/public_keys/<key-id>.pub`.
3. Import the dataset with verification:
   ```bash
   ./wb sync import data/public_sync --peer origin
   ```
   Only fall back to `--allow-unsigned` if you must ingest historical unsigned bundles.

The signature file stores the manifest digest plus the signer’s key ID. Keep `.sync/keys/` out of version control and rotate keys with `./wb sync keygen --force` if a secret ever leaks.

### Optional: Hub relay

Instead of syncing via shared folders, you can run the lightweight hub service in this repo (`app/hub/`).

1. Start the hub (once) and configure peers in `.sync/hub_config.json` (see `docs/hub/README.md`).
   ```bash
   ./wb hub serve --config .sync/hub_config.json --host 127.0.0.1 --port 9100
   ```
   (Use `Ctrl+C` to stop; for production, follow the Ubuntu guide under `docs/hub/`.)
2. On each instance, register the hub peer:
   ```bash
   ./wb sync peers add --name hub --url https://hub.example --token <secret> --public-key <base64>
   ```
3. Use the same commands as before:
   ```bash
   ./wb sync push hub
   ./wb sync pull hub
   ```
   The CLI detects `--url` and uploads/downloads bundles via HTTPS, verifying signatures before import.
4. Optional: create an admin token with `./wb hub admin-token --config .sync/hub_config.json` and visit `/admin` on the hub to view peer stats.

### Web-based Sync Control Center

Administrators can now operate sync workflows entirely from the browser:

1. Log in as an admin and open `/admin/sync-control` (there’s a shortcut button on `/sync/public`).
2. Review existing peers, edit tokens/keys, or add new filesystem/hub peers inline.
3. Use the “Push now” / “Pull now” buttons to queue jobs. Status chips update on refresh, and a rolling activity log records who ran what and whether it succeeded.

Jobs reuse the same signing and verification pipeline as the CLI. You can queue a push, continue browsing, and refresh to see the completion state once the background task finishes.

## Send Welcome page
- While signed in, use the “Send Welcome” button (header menu) to generate an invite instantly.
- The page shows the invite link, token, QR code, and optional fields for suggested username/bio to share with the invitee.
- Shared links pre-fill the token when invitees visit `/register`.

## Authentication workflow
1. A user registers with an invite token (unless they are the first user).
2. If the invite was issued by an approved admin (auto-approve default), the user is fully authenticated instantly and receives a logged-in session.
   Otherwise, the user submits their username on the login page, creating an authentication request and half-authenticated session.
3. While waiting, the user lands on a pending dashboard: they can browse existing requests, save private drafts, and view their verification code.
4. The user (or an administrator) completes verification by submitting the generated code, upgrading the session to fully authenticated.
5. Sessions are stored in the database and tracked through the `wb_session_id` cookie.

The CLI exposes helpers for administration:
```bash
./wb create-admin <username>
./wb create-invite --username <admin> --max-uses 3 --expires-in-days 7
./wb session list                              # Inspect pending authentication requests
./wb session approve <request_id>             # Approve a request from the CLI
./wb session deny <request_id>                # Deny a pending request
```

## Request feed basics
- Lightweight JavaScript helpers drive optional in-place updates; initial pages remain server-rendered.
- The feed page loads from `/` and the backing API lives under `/api/requests`.
- Authenticated users can post new requests, optionally sharing a contact email for follow-up.
- Half-authenticated users can submit requests which remain private (`pending` status) until approval.
- Authors and administrators can mark requests as completed; the UI reflects updates instantly.
- Each request has a canonical page at `/requests/<id>` that mirrors feed visibility rules and offers a shareable link.

## Project layout
```
app/
  config.py             # Environment and settings helpers
  db.py                 # Engine factory and session dependency
  dependencies.py       # FastAPI dependency utilities
  main.py               # App factory and router registration
  models.py             # SQLModel tables (users, sessions, requests, invites)
  modules/              # Pluggable feature modules (requests feed)
  routes/               # API + UI routers
  services/             # Domain services (authentication helpers)
static/css/app.css      # Vanilla CSS design system
templates/              # Jinja templates and enhancement-friendly partials
tools/dev.py            # Click CLI (invoked via wb/wb.bat)
wb.py                   # Cross-platform Python launcher
wb / wb.bat             # Thin wrappers for Linux/macOS and Windows
```

## Adding new modules
1. Create a package under `app/modules/<module_name>/` with `services.py` and optional routers.
2. Register the module in `app/modules/__init__.py` so `register_modules()` wires it into the app.
3. Provide templates and static assets under `templates/<module_name>/` and `static/` as needed.
4. Document the feature using the four-step planning process in `docs/plans/`.
5. Add CLI helpers or UI routes when the module requires interactive workflows.

## Deployment notes
- Static assets are served directly by FastAPI; for production behind a proxy, ensure `/static` is cached appropriately.
- Migrate from SQLite to another database by adjusting `DATABASE_URL` in `.env` and ensuring the driver is installed.
- Set `COOKIE_SECURE=true` and supply a strong `SECRET_KEY` before running in production.
