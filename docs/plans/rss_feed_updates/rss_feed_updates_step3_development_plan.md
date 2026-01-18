# RSS Feed Updates – Step 3 Development Plan

1. **Model + token service scaffolding**
   - **Goal**: Persist per-user RSS tokens (one per feed category) plus last-accessed metadata so URLs can be rotated/revoked.
   - **Dependencies**: `app/models.py`, `app/db.py` initialization, future reuse by settings + feed routes.
   - **Expected changes**: Introduce `RssFeedToken` SQLModel (fields: id, user_id FK, category slug, token string, created_at, last_used_at, revoked_at/disabled flag). Add helper module `app/services/rss_feed_token_service.py` with functions like `get_or_create_token(session, user_id, category)`, `rotate_token(session, user_id, category)`, `record_access(session, token_id)` using `secrets.token_urlsafe`. Wire model into `app/db.py` table metadata so `./wb init-db` picks it up.
   - **Verification**: Run `./wb shell` (or Python REPL) to create sample tokens, then rerun `./wb init-db` to ensure table exists; confirm repeated calls return same token until rotated.
   - **Risks**: Need to ensure tokens remain reasonably long (≥32 chars) and indexed for quick lookup; avoid leaking secrets in logs.

2. **Feed catalog + query helpers**
   - **Goal**: Define the RSS feed categories and how each maps to existing request-query helpers.
   - **Dependencies**: `app/modules/requests/services.py`, `app/services/user_attribute_service.py` for invite-circle lookups, channel metric helpers for comment counts.
   - **Expected changes**: Add a centralized catalog (e.g., `RSS_FEED_VARIANTS`) describing slug, label, description, and filter config (`statuses`, `pinned_only`, `include_pending`, `created_by_filter`, etc.). Extend `services.list_requests` (or add companion helper) to accept optional `created_by_ids` and `include_pending=True` when admin tokens request it. For “invite circle” slices reuse `user_attribute_service.list_invitee_user_ids`; for “admin triage” allow pending statuses only if the owning user is admin. Ensure `_serialize_requests`/`RequestResponse` remain the canonical serializer so RSS outputs stay aligned.
   - **Verification**: Unit smoke via `pytest tests/test_services_requests.py::test_list_requests_filters` (add new cases) plus manual `./wb shell` invocation that builds each catalog query and confirms counts match UI filters.
   - **Risks**: Category explosion; ensure we cap the list (e.g., `all-open`, `my-circle`, `completed`, `admin-pending`) and keep rules easy to reason about.

3. **Settings backend for RSS management**
   - **Goal**: Provide authenticated HTML endpoints for viewing/copying/rotating feed URLs.
   - **Dependencies**: `app/routes/ui/__init__.py` (settings routes), `templates/settings/*`, new token service from Stage 1, menu helpers for navigation label.
   - **Expected changes**: Add `/settings/notifications` (GET) and `/settings/notifications/rotate` (POST) handlers. GET builds context with available feed variants, calling `rss_feed_token_service.get_or_create_token` per category and formatting absolute URLs (reusing `request.url_for` + `SITE_URL`). POST rotates the selected category’s token and redirects back with a flash message. Update `_build_account_settings_context` or new helper to include session metadata for that page; add nav link from account settings to notifications if needed.
   - **Verification**: With server running, visit `/settings/notifications`, ensure tokens render, click rotate to see new URL, and verify old link is invalidated by fetching feed (Stage 5).
   - **Risks**: Accidentally leaking tokens in referer headers—ensure rotation POST redirects to same page without query params and the template avoids embedding tokens in button actions (only copy fields).

4. **Template + UX updates**
   - **Goal**: Render RSS management UI with copy buttons and short descriptions.
   - **Dependencies**: `templates/settings/account.html` (or new `templates/settings/notifications.html`), base styles in `static/css/app.css`.
   - **Expected changes**: Create `settings/notifications.html` with a card/stack layout listing each feed variant (name, description, scope tags), a readonly input or button showing the feed URL, and a “Regenerate” form per item. Include quick instructions plus last-accessed timestamps pulled from Stage 1 data. If necessary add a `settings` subnav partial linking “Account” / “Notifications”.
   - **Verification**: Load page in browser, confirm accessible markup (labels, sr-only text) and that tokens aren’t truncated; run existing CSS build if new classes require it.
   - **Risks**: Long URLs breaking layout—use CSS to wrap/scroll; ensure we guard against accidental copy via select-all.

5. **RSS delivery endpoints**
   - **Goal**: Serve XML feeds per token/category using canonical request serialization.
   - **Dependencies**: FastAPI router registration (likely new `app/routes/rss.py`), token service, request services, site URL config, `RequestResponse` serializer.
   - **Expected changes**: Create router under `/feeds/{token}/{category}.xml`. Handler validates token (ensuring category matches and route isn’t disabled), loads viewer user, enforces admin-only slices, queries appropriate requests via Stage 2 helpers, then renders RSS with channel metadata (site title, description, build date). Use a lightweight XML builder (e.g., `xml.etree.ElementTree`) and wrap response with `Response(content, media_type="application/rss+xml")`. Record last-accessed timestamps for auditing. Respect caching headers (short TTL) and ensure request links point to canonical `/requests/{id}`. Include statuses/pin info in `<category>` or `<title>`.
   - **Verification**: Manually curl each feed, confirm 200/`application/rss+xml`, and drop into an RSS reader (or `feedparser` in REPL) to ensure valid XML with expected entries per category. Rotate token to confirm old URL now 404s.
   - **Risks**: Performance spikes if feeds are polled aggressively; add simple rate limiting (FastAPI dependency) or rely on token-specific caching headers. Validate user scope carefully to avoid leaking pending/admin data.

6. **Auditing + docs**
   - **Goal**: Surface minimal audit metadata and help text so operators can monitor feed usage.
   - **Dependencies**: Token service (last_used_at), settings template, README or in-app instructions.
   - **Expected changes**: Update token service to store `last_used_at` on each feed request. Display this timestamp in settings UI (e.g., “Last read 5m ago”). Add short instructions (maybe `templates/settings/partials/rss_help.html`) and mention RSS feeds in `README.md` or `docs/user_guides`. Consider logging suspicious access (invalid token attempts) in FastAPI logger.
   - **Verification**: Fetch a feed, reload settings, ensure “Last read” updates. Review docs locally for accuracy.
   - **Risks**: Forgetting to mention admin-only categories; doc drift if we later add more feeds.
