# Invite Frontend UI — Step 1 Solution Assessment

**Problem statement**
- Authenticated users (not just admins) lack an in-app way to generate invite tokens; they must use CLI/API despite the recent shareable-link support.

**Option A – Add invite page accessible via button/link (preferred)**
- Pros: Dedicated page can immediately show generated link/QR and include optional fields (invitee username/bio); reuses existing backend token creation.
- Cons: Slightly more navigation work than modal; must ensure server generates invite link on page load.

**Option B – Modal workflow with pre-generated link**
- Pros: Minimal navigation; fast access within current page.
- Cons: Harder to accommodate optional bio/username fields without clutter; doesn’t meet explicit link-to-page requirement.

**Option C – Embed form inline in existing dashboard section**
- Pros: Simple implementation; no modal logic.
- Cons: UI clutter; share output less prominent; harder to reuse.

**Recommendation**
- Implement Option A: add a “Send Welcome” button/link for authenticated users that navigates to a dedicated invite page. Upon arrival, the page generates (or fetches) a token, displays link + QR, and lets the inviter optionally fill in suggested username/bio to pass along.
