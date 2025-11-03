# Invite Link Generation — Step 4 Implementation Summary

## Stage 1: Base URL helper
- Added `app/url_utils.py` providing `build_invite_link` that uses the incoming request origin, falling back to `SITE_URL`.

## Stage 2: API/CLI integration
- `/auth/invites` now returns a `link` property so callers receive a ready-to-share URL.
- CLI `./wb create-invite` prints the full invite link alongside the token for immediate sharing.

## Stage 3: Documentation updates
- Introduced `SITE_URL` setting in README and developer cheatsheet, explaining how invite link generation determines the host.

## Stage 4: QA
- `pytest` (suite currently reports "no tests ran").
- Manual verification recommended: run `./wb create-invite` and ensure the generated link includes the expected host.
