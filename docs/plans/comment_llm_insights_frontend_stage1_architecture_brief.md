# Stage 1 – Architecture Brief: Comment LLM Insights Frontend

## Option A – Admin-only dashboards (SPA widgets)
- Render a new `/admin/comment-insights` page powered by the existing JSON API (`/api/admin/comment-insights`).
- Use HTMX/Alpine components to list runs, show per-run tables, and inline comment summaries.
- Pros: Minimal backend work; reuses SQLite + API; can paginate client-side.
- Cons: Data only visible to admins; no integration with request-detail pages; limited discoverability.

## Option B – Embed insights into request detail pages
- Extend request detail view to fetch comment analyses on demand (per comment) via AJAX + caching.
- Pros: High relevance (insights next to original comment); supports non-admin ops once permissions relaxed.
- Cons: Heavier load (N HTTP calls per request) without batching; requires careful UI design to avoid clutter; more auth considerations.

## Option C – Hybrid: Admin insights dashboard + inline preview hooks
- Ship dedicated admin dashboard for bulk browsing plus lightweight hooks on request detail pages (badge/tooltip) that link to the admin view.
- Pros: Fast to implement (dashboard first) while paving path for inline experiences; keeps heavy data out of primary UI.
- Cons: Two surfaces to maintain; bridging permissions between admin + general views needs planning.

## Chosen Direction: Option C
- Sequence: build admin dashboard as the authoritative browser (runs → analyses → link to request). Later add inline indicator (icon linking to admin view or showing summary when hovered) on request detail page for admins.

## Key Components / Contracts
- API: `/api/admin/comment-insights` (existing), ensure JSON shape stable.
- UI: new template (Jinja/HTMX) under `templates/admin/comment_insights.html` with sections: run list, run detail table, comment detail modal.
- JS: small HTMX endpoints to fetch run detail and comment summary to avoid full page reloads.

## Open Questions / Unknowns
- Pagination strategy: server-side vs client-side (likely server pagination via query params).
- Authorization: should ops (non-admin) get read access? (default deny; revisit after admin launch.)
- Export needs: CSV/clipboard for run analyses? (future capability.)

## Risks
- DB file locking if multiple admin users hammer the dashboard simultaneously (mitigated by WAL mode).
- UI clutter if inline preview is added without a thoughtful layout; stage and gather feedback.
