# Invite Link Generation — Step 1 Solution Assessment

**Problem statement**
- Users want a ready-to-share invite link that already contains their token and the correct server URL, avoiding manual copy/paste.

**Option A – Enhance existing invite modal with link builder (preferred)**
- Pros: Minimal change—reuses invite generation flow; just adds derived link text using request URL or configured base; no new routes required.
- Cons: Requires careful handling of canonical host in multi-environment setups.

**Option B – Dedicated “copy invite link” endpoint**
- Pros: Returns fully qualified URLs via JSON; can be reused by CLI/UI; clearer separation.
- Cons: Adds another API surface; needs auth/permission checks.

**Option C – CLI-only enhancement**
- Pros: Quick to ship; `./wb create-invite` prints a full link.
- Cons: Doesn’t help web users clicking “Generate invite” in the UI.

**Recommendation**
- Implement Option A: when an invite token is created via the existing UI modal, display a full URL assembled from the current request origin (fallback to config). This keeps effort low while meeting user needs.
