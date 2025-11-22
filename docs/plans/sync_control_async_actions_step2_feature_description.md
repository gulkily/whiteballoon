# Sync Control Async Actions — Step 2: Feature Description

**Problem**
Manual push/pull controls on `/admin/sync-control` currently submit full-page POSTs. Admins lose context, interrupting real-time monitoring and delaying follow-up actions while the page reloads.

**User stories**
- As an administrator, I want to start a manual push without leaving the page so I can immediately monitor the job tile for progress.
- As an administrator, I want the push/pull buttons to stay disabled until their corresponding job completes so I don’t trigger duplicate jobs.
- As an administrator, I want to see a clear error inline if a manual sync fails to enqueue, so I know to retry or investigate.

**Core requirements**
- Intercept push/pull form submissions with JavaScript; send the POST using `fetch` (same endpoint, CSRF token preserved) and prevent navigation on success.
- Display a non-intrusive inline notification or message near the controls when the request is accepted or when it fails (fallback message for errors/timeouts).
- Ensure buttons re-enable only once the real-time job updates indicate completion or when the request fails before enqueueing.

**User flow**
1. Admin clicks “Push now” or “Pull now”.
2. JS intercepts submit, disables the button, shows “Starting…” feedback, and posts to the existing endpoint.
3. On success, the UI waits for the job status tile to update via SSE/polling; the button stays disabled until the tile reports a terminal state.
4. On failure, an inline error is shown and the button re-enables for another attempt.

**Success criteria**
- Clicking push/pull no longer refreshes the page in modern browsers with JS enabled.
- Real-time tiles update as before, with buttons reflecting job state (disabled during active job, enabled otherwise).
- Error cases (network failure or non-2xx response) surface a visible message without a reload.
- Non-JS browsers still submit forms and reload as today.
