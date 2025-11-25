## Stage 1 – Settings route + template scaffold
- Dependencies: Existing auth/session helpers; profile page context.
- Changes: Add `/settings/account` GET route (requires auth) returning a new template with current email + photo preview; stub POST handler with no-op validation.
- Verification: FastAPI route unit test ensuring only authenticated users reach the page; manual load in dev.
- Risks: Template duplication with profile page; forgetting to reuse shared layout components.

## Stage 2 – Email update backend
- Dependencies: Stage 1 scaffold.
- Changes: Implement POST form handling for contact email—validate format, trim, persist to `User.contact_email`, show success/error message; ensure CSRF/token strategy consistent with existing forms.
- Verification: Unit/integration test for valid + invalid email submission; manual form submission.
- Risks: Email validation edge cases; error messaging leaking details.

## Stage 3 – Photo upload pipeline
- Dependencies: Stage 1 template, existing storage utilities.
- Changes: Add file input handling to POST route—validate MIME/size, store via current upload helper (e.g., `static/uploads`), update `PROFILE_PHOTO_URL_KEY` attribute; handle removal option.
- Verification: Manual upload test, ensure new avatar appears on profile/invite map; optional unit test for attribute write.
- Risks: Large file handling, storage cleanup, security (MIME sniffing, path traversal).

## Stage 4 – UI polish + feedback states
- Dependencies: Stages 1-3.
- Changes: Add inline success/error alerts, show current photo thumbnail, disable submit while processing, provide copy about recommended sizes; ensure responsive layout.
- Verification: Manual UX walkthrough across desktop/mobile.
- Risks: Layout regression on narrow screens; unclear messaging.

## Stage 5 – Regression sweep & documentation
- Dependencies: Prior stages complete.
- Changes: Update profile page or docs to mention editable settings; ensure invite map avatars reflect new uploads; summarize verification in Step 4 doc.
- Verification: Run targeted pytest, manual regression on profile + invite map.
- Risks: Overlooking caches (invite map) leading to stale avatars; missing documentation of limits.
