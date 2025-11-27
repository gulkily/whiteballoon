# Sync Control Async Actions — Step 3: Development Plan

1. **Capture peer-action form context**
   - *Changes*: In `templates/sync/control.html`, add identifiers/hooks (e.g., `data-job-form`, `data-job-message`) around push/pull forms for JS to target; ensure CSRF token fields remain untouched.
   - *Verification*: Load `/admin/sync-control` and confirm DOM contains the expected data attributes for each peer card.
   - *Risks*: Overlapping dataset names; ensure attributes don’t collide with existing job control hooks.

2. **Enhance realtime-status JS with async submit handler**
   - *Changes*: Extend `static/js/realtime-status.js` to listen for `submit` on elements marked for async mode; prevent default, send `fetch` POST using existing form action/method, include form data; disable button, show pending message, and surface errors inline.
   - *Verification*: Trigger push/pull in dev inspector and confirm no page reload, network request completes, and inline status updates.
   - *Risks*: Failed requests leaving controls disabled; mitigate with error catch and re-enable logic.

3. **Maintain progressive enhancement fallback**
   - *Changes*: Ensure JS only intercepts when `window.fetch` is available; otherwise allow default form submission; add small inline message container for serverside fallback.
   - *Verification*: Temporarily disable JS (or force error) and confirm form still reloads the page, enqueuing jobs as today.
   - *Risks*: Double-submission if both handlers fire; ensure handler returns early when JS interception is skipped.
