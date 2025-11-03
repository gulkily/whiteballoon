## Stage 1 – Add shared profile view
- Introduced `/people/{username}` in `app/routes/ui.py` to let signed-in members load another user’s profile with safe contact visibility rules.
- Created `templates/profile/show.html` to render the shared profile layout, including fallback messaging when contact details are restricted.

### Testing
- Manual: Pending — need to load `/people/{username}` as admin/member/half-auth to validate visibility and 404 handling.

## Stage 2 – Link creator names in server render
- Wrapped the request creator label in `templates/requests/partials/item.html` with a profile link when a username is available, preserving the existing fallback text otherwise.

### Testing
- Manual: Pending — reload dashboard and verify the creator label is keyboard focusable and navigates correctly; confirm pending view handles missing usernames gracefully.

## Stage 3 – Sync client renderer and styling
- Mirrored the anchor markup inside `static/js/request-feed.js` so live updates match server-rendered cards, including encoded URLs and accessible titles.
- Adjusted styles in `static/css/app.css` to give linked creator names hover/focus treatments without disrupting the layout.

### Testing
- Manual: Pending — create a request to force client refresh and ensure the link renders identically; tab through to confirm focus styling.

## Stage 4 – Verification sweep
- Attempted to run automated tests (`pytest`), but the command is not available in this environment.
- Manual validation deferred to an environment with the app running: need to check admin/member/half-auth navigation, link focus, and 404 handling for missing users.

### Testing
- Automated: `pytest` (not run — command missing).
- Manual: Pending — requires interactive session to exercise profile navigation flows.
