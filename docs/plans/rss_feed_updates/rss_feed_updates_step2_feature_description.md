# RSS Feed Updates – Step 2 Feature Description

## Problem
Users and admins currently have no subscription mechanism for help-request activity, forcing them to log into the UI to check for updates. We need RSS feeds that mirror each person’s permissions and category filters so everyone can stay current from any reader.

## User stories
- As a fully authenticated member, I want RSS feeds for the request types I care about so I can help quickly without refreshing the site.
- As an admin, I want per-scope and admin-triage RSS feeds so I can monitor pending verifications, high-priority requests, and completions from one dashboard.
- As any user, I want the ability to regenerate or revoke RSS URLs so I can lock down access if a token leaks.

## Core requirements
- Provide multiple RSS categories per user (e.g., “All accessible requests,” “Pending verifications/admin triage,” “My invites,” “Completed/archived”), each with its own tokenized endpoint.
- Scope every feed to the subscriber’s existing permissions; feeds must never expose requests the user cannot already see in the UI or `/api/requests`.
- Offer discoverability and management inside the authenticated settings area (view/copy URLs, regenerate tokens, disable feeds).
- Deliver structured RSS (title, summary, status, timestamps, canonical request link) that updates as soon as the underlying data changes.
- Audit token usage minimally (last accessed timestamp) so admins can monitor misuse and expire compromised feeds.

## Shared component inventory
- `app/modules/requests/routes.py` + `_serialize_requests` helper: canonical API/serialization for request listings. **Reuse** to power RSS payloads so filtering, pinning, and scopes stay consistent.
- `templates/requests/index.html` + `static/js/request-feed.js`: existing request feed UX already organizes requests by category. **Reuse** the same filter definitions to decide which RSS variants we expose (e.g., open, completed, admin pending) instead of inventing new slices.
- `app/routes/ui/settings.py` + `templates/settings/notifications.html` (or equivalent settings view): **Extend** to surface RSS management, since this is where members already manage invite links/security.
- `/api/requests` endpoint + any pending request APIs documented in `docs/spec.md`: **Reuse** data contracts so feed consumers receive the same fields (title, status, member info) that API clients get today.

## Simple user flow
1. Signed-in user opens Settings → Notifications (new RSS section) and sees a list of available feed categories with per-category secret URLs.
2. User copies the desired RSS URL into their reader; optionally regenerates a token if they need a fresh link.
3. Reader polls the RSS endpoint; the server validates the token, applies the user’s scope filters, and returns the category-specific feed.
4. When requests change (new, updated, completed) the next poll reflects those entries with links back to the canonical request detail page.
5. Admins can revoke or rotate tokens at any time, immediately invalidating old feed URLs.

## Success criteria
- Every authenticated user can view at least three feed categories (all accessible requests, invitation circle, completed/pinned or admin-triage) with unique URLs tied to their account.
- RSS feeds return within <1 s for typical categories and match the counts/ordering seen on the web feed for the same filters.
- Token rotation works without server restarts and invalidates old URLs within one poll interval.
- No feed leaks data across scopes in manual spot checks (admin vs. regular member vs. pending user).
- Documentation (help snippet in Settings) explains how to subscribe and manage tokens.
