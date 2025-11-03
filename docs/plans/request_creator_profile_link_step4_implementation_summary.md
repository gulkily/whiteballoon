## Stage 1 – Add shared profile view
- Introduced `/people/{username}` in `app/routes/ui.py` to let signed-in members load another user’s profile with safe contact visibility rules.
- Created `templates/profile/show.html` to render the shared profile layout, including fallback messaging when contact details are restricted.

### Testing
- Manual: Pending — need to load `/people/{username}` as admin/member/half-auth to validate visibility and 404 handling.
