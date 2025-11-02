## Overview
- Derived a reusable session-role descriptor so templates know whether the viewer is an administrator, fully approved member, or still pending verification.
- Surfaced the role indicator in the primary navigation for both the main request dashboard and the pending-approval view.

## Implementation notes
- Added `describe_session_role` helper in `app/routes/ui.py` and threaded the resulting label through the home contexts alongside existing request data.
- Updated `requests/index.html` and `requests/pending.html` navigation blocks to render a compact badge showing the current role before the sign-out control.

## Testing
- Automated: Not run (Python tooling unavailable in this environment).
- Manual: Pending — should verify badge text for admin, member, and half-auth sessions after deployment.
