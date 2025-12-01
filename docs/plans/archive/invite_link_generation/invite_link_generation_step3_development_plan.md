# Invite Link Generation — Step 3 Development Plan

1. **Stage 1: Determine base URL helper**
   - Changes: Add utility (e.g., in `app/routes/ui.py` or shared helper) that builds the absolute `/register` URL from `Request.base_url`, falling back to `SITE_URL` setting.
   - Testing: Manual check in dev + unit test for fallback.

2. **Stage 2: Update invite modal/template**
   - Changes: Pass computed link to `invite_modal.html` (or equivalent) and add copy button/anchor alongside QR code; ensure token query parameter pre-fills registration form.
   - Testing: Manual generation; confirm link copies correctly.

3. **Stage 3: CLI output & docs**
   - Changes: Enhance `./wb create-invite` to print the full link using config base URL; update README/cheatsheet (and code tour if needed).
   - Testing: Run CLI command; verify documentation references.

4. **Stage 4: QA**
   - Run `pytest`; manual browser test to share link.
