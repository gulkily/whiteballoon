# Profile Invite Photo Integration — Step 3 Development Plan

1. **Stage 1: Data Association**
   - Update onboarding logic to copy invite photo reference onto the user profile/avatar field.
   - Handle cases where multiple invites exist; prefer the invite used for registration.
   - Verification: unit or integration test for user creation with invite personalization.

2. **Stage 2: Profile Display Update**
   - Render the invite photo on profile pages when available; fallback to current initials avatar.
   - Ensure templates handle alt text and responsive sizing.
   - Verification: manual profile view with/without photo.

3. **Stage 3: API/Serialization (if needed)**
   - Expose avatar URL in any existing user serializers (e.g., account nav) so other components can use it later.
   - Verification: manual nav inspection or unit test.

4. **Stage 4: QA & Documentation**
   - Smoke test registration with invite, confirm avatar appears; repeat with no photo to ensure fallback.
   - Document behaviour in README or design notes.
