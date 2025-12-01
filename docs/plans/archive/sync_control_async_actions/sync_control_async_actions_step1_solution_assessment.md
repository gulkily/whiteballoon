# Sync Control Async Actions — Step 1: Solution Assessment

**Problem statement**: On `/admin/sync-control`, the "Push now" and "Pull now" forms trigger full page reloads, breaking context while the real-time job tiles already stream status updates.

**Solution options**
- **Option A – Progressive enhancement via JavaScript fetch**
  - Pros: Keep existing server handlers and CSRF tokens; intercept submit, post via `fetch`, and update local job status/disabled state without reload; minimal template churn.
  - Cons: Requires careful error handling and duplicate logic for fallback (non-JS users still post normally).
- **Option B – Convert buttons into API-triggering buttons**
  - Pros: Replace forms with `<button type="button">` that call new JSON endpoints; simplifies markup and avoids hidden inputs.
  - Cons: Needs new API routes or refactors; loses built-in CSRF protection from forms unless manually reproduced.
- **Option C – Adopt HTMX or Stimulus component for peer actions**
  - Pros: Could standardize interactivity for other admin controls and manage spinners/optimistic UI declaratively.
  - Cons: Introduces new dependency or framework overhead for a small feature; longer ramp-up.

**Recommendation**: Choose **Option A**. Intercepting submits lets us keep existing POST endpoints and CSRF flow while providing the no-reload experience. The new client logic can live alongside `realtime-status.js`, enabling optimistic job state updates and graceful fallbacks.
