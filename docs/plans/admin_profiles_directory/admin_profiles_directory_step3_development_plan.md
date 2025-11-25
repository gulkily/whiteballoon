# Admin Profile Directory – Step 3 Development Plan

## Stage 1 – Admin Route + Template Skeleton
- **Goal**: Add `/admin/profiles` route gated for admins and render a placeholder template that lists users without filtering/pagination.
- **Dependencies**: Existing admin auth guard; `User` model + SQLModel session helpers.
- **Changes**: Add route handler in appropriate admin module (`app/routes/admin.py` or similar), load all users ordered by `created_at` desc, render new template at `templates/admin/profiles.html`.
- **Verification**: Log in as admin, visit `/admin/profiles`, confirm list renders, confirm non-admin receives 403.
- **Risks**: Query may load too many rows; note for next stage.

## Stage 2 – Pagination + Filtering
- **Goal**: Add server-side pagination (page size 25) and optional filters for username/contact email substring.
- **Dependencies**: Stage 1 route/template.
- **Changes**: Accept query params (`page`, `q`, `contact`), build SQLModel query with `ilike` filters, compute total pages, pass pagination data to template, add a filter form.
- **Verification**: Use sample data to confirm filtering and pagination boundaries; ensure invalid page falls back gracefully.
- **Risks**: SQLite `ilike` needs case-folding; rely on `func.lower` if necessary.

## Stage 3 – Row Actions and Context Links
- **Goal**: Provide actionable links per row (view requests filtered by user, link to invite history if available, mailto for contact email).
- **Dependencies**: Stage 2 template populates row fields.
- **Changes**: Add icons/buttons linking to `/requests?user=<id>` (or add a new admin view), `mailto:` links, include sync scope/status chips.
- **Verification**: Manually click each action; ensure missing data handled gracefully (no contact email, no requests link if route absent).
- **Risks**: Some linked routes might not exist—if so, add TODO/placeholder text.

## Stage 4 – Access Control + Documentation
- **Goal**: Harden permission checks, add tests if feasible, and document the new page in admin guide/readme.
- **Dependencies**: Previous stages complete.
- **Changes**: Ensure route decorator enforces admin role, add unit/functional test for admin vs non-admin access, update README/admin docs.
- **Verification**: Run relevant tests (if existing harness) or manual check; confirm documentation references the new page.
- **Risks**: Limited automated test scaffolding; fallback to manual verification.
