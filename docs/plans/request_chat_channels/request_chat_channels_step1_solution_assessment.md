# Request Chat Channels – Step 1 Solution Assessment

**Problem**: Researchers need a Slack-style flow where each request is treated as a channel and its comments render as a live chat log to speed triage conversations.

**Option A – Retrofit the existing request detail view**
- Pros: Reuses current routing/state/data loaders; minimal navigation changes so links keep working; faster to ship because only one request is on screen at a time.
- Cons: Does not solve multi-request context switching; constrained by existing column grid so Slack metaphors (channel list, composer, presence) feel bolted on; heavier JS needed to simulate live chat within legacy templates.

**Option B – New dual-pane “Requests as Channels” workspace**
- Pros: Purpose-built channel list + chat pane matches Slack mental model; enables keyboard shortcuts, unread badges, presence, and fast request hopping; can share chat components with future messaging features.
- Cons: Requires new route, layout, and state container; needs virtualization/infinite scroll to keep large chat histories smooth; onboarding links must map legacy request URLs to the new surface.

**Option C – Embed Slack-like chat inside the existing request index**
- Pros: Keeps list of requests visible while letting users open a sliding chat drawer; minimal navigation churn for users already living in the index table; cheaper than a full workspace rewrite.
- Cons: Drawer UX limits vertical space for chat, hurting readability; complex focus management on small screens; duplicative logic because both index filters and drawer chat need their own data lifecycles.

**Recommendation**: Option B. A dedicated workspace best matches the “channels + chat log” objective, unlocks faster request hopping, and creates reusable real-time chat components without fighting legacy layouts.
