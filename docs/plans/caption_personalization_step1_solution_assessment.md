# Caption Personalization · Step 1 Solution Assessment

**Problem statement**: Informational captions help orient new members, but long-term users find them cluttered— we need a way to keep onboarding context while decluttering experienced users’ UI.

**Option A – Progressive disclosure based on dismissals**
- Add a tiny thumbs-up “Got it” button on each caption; once dismissed, store the preference per user and hide future renders.
- Pros: Easy mental model, per-caption granularity, keeps helpful text for new/occasional users.
- Cons: Requires adding state tracking (e.g., user attributes) and dismiss controls on many components.

**Option B – Profile-level “minimal UI” toggle**
- Provide a setting (“Hide helper captions”) in account preferences; when enabled, globally suppress non-critical caption blocks.
- Pros: Simple implementation, one toggle handles all captions, power users control the experience.
- Cons: Binary choice—some captions might still be useful; users must discover the setting manually.

**Option C – Contextual aging**
- Automatically fade captions after the user completes key milestones (e.g., published X requests, logged in > N times) without manual action.
- Pros: Zero effort for seasoned users; keeps captions for truly new folks.
- Cons: Harder to explain, might hide captions prematurely (e.g., mentors who don’t post often) and lacks manual override.

**Recommendation**: Combine Options A + B. Start with a global “Hide helper captions” toggle so experienced users can opt out immediately, then layer per-caption dismissals over time for finer control—covers both self-directed power users and occasional members who just want to hide a specific blurb.
