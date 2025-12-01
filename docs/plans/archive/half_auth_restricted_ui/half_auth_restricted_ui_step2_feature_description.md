# Half-Authenticated Restricted UI – Feature Description

- **Problem**: Users who submit their username are left at `/` with a half-authenticated session but see the logged-out experience; we need a clear, restricted UI for them until approval completes.
- **User stories**:
  - As a user awaiting approval, I want to see that my request is pending so I’m not confused about the next step.
  - As an administrator, I want pending users to stay on a holding view so they don’t interact with the main feed until approved.
  - As a developer, I want the UI to reflect session state (half vs full) so I can reason about access control.
- **Core requirements**:
  - Detect half-authenticated sessions on `/` and render a dedicated holding page (e.g., “Waiting for approval”) instead of the logged-out landing.
  - Include instructions/action such as showing the pending verification code or a refresh hint.
  - Ensure fully authenticated users still see the feed; logged-out users still see the welcome page.
  - Keep the spec (`docs/spec.md`) updated to document the new state and flow.
- **User flow**:
  1. User submits username at `/login`; system creates half-auth session and verification code.
  2. User returns to `/`; pending view displays existing requests in read-only mode, the verification code, and next steps while awaiting approval.
  3. Once approval is completed (verify code succeeds), redirect to `/` shows the full interactive dashboard.
- **Success criteria**:
  - Half-authenticated users consistently see the pending state page and cannot interact with the full feed.
  - Full-auth users still get the normal dashboard; logged-out users get the welcome splash.
  - Spec and documentation reflect the three UI states (logged out, half-auth pending, fully authenticated).
