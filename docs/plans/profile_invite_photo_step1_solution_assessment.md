# Profile Invite Photo Integration — Step 1 Solution Assessment

**Problem statement**
- Invite issuers can now upload a welcome photo, but we never surface that asset on the invited user’s profile; the image sits unused.

**Option A – Auto-populate profile avatar from invite photo (recommended)**
- Pros: Leverages existing asset, provides instant personalization, minimal UI changes (just display if present).
- Cons: Requires linking invite personalization metadata to the user record and handling fallback/opt-out.

**Option B – Manual opt-in via profile editor**
- Pros: Gives users explicit control before showing the photo.
- Cons: Adds friction (extra step) and doesn’t solve the “empty profile” on first visit; editors don’t exist yet.

**Option C – Dedicated “Welcome gallery” separate from profile**
- Pros: Allows curated onboarding flow without touching core profile layout.
- Cons: More design + navigation changes; doesn’t improve the standard profile page.

**Recommendation**
- Pursue Option A: automatically populate the user’s profile avatar with the invite photo when available, while keeping fallbacks in place and allowing future overrides.
