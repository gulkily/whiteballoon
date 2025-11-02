## Stage 1 – Provide username + role context to templates
- **Goal**: Ensure all authenticated templates receive both the user’s username and a normalized role descriptor.
- **Dependencies**: None (builds on existing `SessionUser` context; reuse `describe_session_role` helper).
- **Changes**: Update `app/routes/ui.py` to include `session_username` (or similar) in the context dictionaries returned for home and pending views. Confirm the helper can be shared with future profile routes.
- **Testing**: Manual check via shell/logs; automated optional.
- **Risks**: Forgetting half-authenticated path or duplicating logic across views.

## Stage 2 – Update navigation UI
- **Goal**: Display username together with the role badge and introduce a profile icon entry point in the header.
- **Dependencies**: Stage 1.
- **Changes**: Modify `templates/base.html` (nav layout) or relevant blocks to render username text adjacent to the role badge and add a profile icon/link on the right side. Ensure spacing remains responsive. 
- **Testing**: Manual smoke test on desktop/mobile widths for admin/member/pending sessions.
- **Risks**: Layout overflow or icon misalignment, accidentally surfacing controls on logged-out pages.

## Stage 3 – Add profile view/route
- **Goal**: Serve a new profile page showing the current account’s key details.
- **Dependencies**: Stage 1.
- **Changes**: Add a route under `app/routes/ui.py` (e.g., `/profile`) guarded by `require_session_user`; render a new template `templates/profile/index.html` containing username, role label, and placeholder text for future settings.
- **Testing**: Manual navigate to `/profile` as each role; confirm unauthorized sessions redirect/login as needed.
- **Risks**: Missing authorization guard, inconsistent context structure, or breadcrumb collisions with existing routes.
