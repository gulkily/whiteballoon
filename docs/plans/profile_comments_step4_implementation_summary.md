# Profile Comments – Step 4 Implementation Summary

## Stage 1 – Inline recent comments for admins
- Changes: Added `request_comment_service.list_recent_comments_for_user` plus a hard cap constant, piped the data into `/people/{username}` for admins, and rendered a "Recent comments" card that shows up to five latest entries with scope badges and request links. Added lightweight profile-specific styles for the new list.
- Verification: Seeded a test profile with seven comments across two requests, loaded `/people/<username>` as an admin, and confirmed the newest five render chronologically with working request links and the placeholder “Full history coming soon” action. Viewed as a non-admin to ensure the block stays hidden.
