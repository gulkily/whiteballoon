# UI Route Package Layout

The UI FastAPI router is being decomposed into cohesive packages so each surface
has a dedicated module. The top-level `app.routes.ui.__init__` continues to
register all routes, but individual handlers are moving into the packages below:

- `auth/` – authentication flows (`/login`, `/register`) – invite-specific pages now live in `invite/`.
- `requests/` – feed, detail, channels, and recurring request routes (`/requests*`)
- `people/` – member directory + profile comments (`/people/*`)
- `profile/` – self-profile + highlights (`/profile*`)
- `browse/` – aggregated browse/search endpoint (`/browse*`)
- `settings/` – account + notification settings (`/settings*`)
- `comments/` – comment detail and related actions (`/comments*`)
- `invite/` – invite map + new invite flows (`/invite*`)
- `branding.py` – standalone logo variants under `/brand/*`
- `api/` – lightweight UI JSON helpers under `/api/*` (metrics, future JSON utilities)
- `admin.py` – remains the orchestrator for `/admin` routes until each panel
  is extracted into `app/routes/ui/admin/{section}.py`.

Each package exposes a FastAPI `router` instance so `app.routes.ui.__init__`
can mount it once the corresponding handlers move over. This keeps imports tidy
and clarifies where new routes should live.
