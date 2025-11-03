# Dark Mode Support — Step 1 Solution Assessment

**Problem statement**
- Users cannot toggle between light and dark themes or follow their system preference, limiting accessibility and comfort, especially in low-light environments.

**Option A – CSS variables + prefers-color-scheme with manual toggle (preferred)**
- Pros: Leverages existing CSS variables; enables auto detection via `prefers-color-scheme` plus a user toggle stored in `localStorage`; minimal backend changes.
- Cons: Requires refactoring styles to ensure full variable coverage; must ship lightweight JS to manage toggle/state.

**Option B – Theme swap via separate stylesheets**
- Pros: Straightforward inclusion of dedicated light/dark CSS files; toggle can simply swap stylesheet hrefs; limited changes to existing base styles.
- Cons: Risk of styles drifting between files; harder to maintain overrides; slower first paint due to extra requests.

**Option C – Server-side theme rendering**
- Pros: Stores user preference on the server (cookie/session), allowing SSR to deliver correct theme without flash; central control for future deployments.
- Cons: Requires auth-aware rendering; introduces more backend logic and persistent storage; more complex to implement quickly.

**Recommendation**
- Implement Option A: extend the CSS variable system with dark theme values, use `prefers-color-scheme` for auto detection, and add a client-side toggle that persists preference. This balances UX quality with implementation speed and keeps maintenance manageable.
