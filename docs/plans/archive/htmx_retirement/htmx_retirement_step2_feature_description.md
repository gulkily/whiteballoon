# HTMX Retirement – Feature Description

- **Problem**: Remove the HTMX dependency while preserving dynamic request feed interactions, ensuring the registration workflow and authenticated dashboard remain intuitive.
- **User stories**:
  - As an authenticated member, I want to create and complete requests without full page reloads so that the experience remains fast after HTMX is removed.
  - As a new registrant, I want my optional first request to post successfully even without HTMX so that onboarding stays smooth.
  - As a developer, I want the frontend to rely on minimal JavaScript so that maintenance and future enhancements are straightforward.
- **Core requirements**:
  - Replace HTMX interactions with lightweight JavaScript or URL-based workflows that keep the UX responsive.
  - Ensure request creation, completion, and list refreshes work without HTMX on desktop and mobile while keeping the initial page fully rendered on first load.
  - Remove the HTMX script tag from templates and drop any dependency references in docs.
  - Update tests/docs to reflect the new interaction model.
- **User flow**:
  1. User navigates to the dashboard; button reveals request form via JavaScript-controlled toggle.
  2. User submits a request; the page updates (via JS or redirect) to show the new entry.
  3. User marks a request complete; UI reflects the change without HTMX.
- **Success criteria**:
  - No HTMX assets or attributes remain in the codebase.
  - Request lifecycle actions remain smooth with minimal reloads.
  - Registration continues to support optional first request posting.
  - Documentation accurately describes the new JS/interaction approach.
