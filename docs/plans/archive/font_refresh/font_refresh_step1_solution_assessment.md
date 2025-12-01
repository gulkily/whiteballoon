# Font Refresh — Step 1 Solution Assessment

**Problem statement**
- The current font stack (system sans only) feels generic. We want typography that better reflects a welcoming mutual-aid community while avoiding third-party font hosts.

**Option A – Self-host an open-source typeface (preferred)**
- Pros: We can select a warm sans/serif combo (e.g., Plus Jakarta Sans, Inter Display) and bundle WOFF2 files locally. Offers brand personality with minimal performance cost.
- Cons: Need to manage licensing and generate font files ourselves; slightly more setup.

**Option B – Enhance system stack styling only**
- Pros: Zero asset overhead; rely on weight/letter-spacing tweaks and CSS features (e.g., font-feature-settings) for polish.
- Cons: Limited ability to differentiate; results may vary per OS.

**Option C – Create custom variable font from scratch**
- Pros: Fully unique; precise control.
- Cons: High effort; requires specialized tools and time; unnecessary for current needs.

**Recommendation**
- Pursue Option A: select one primary display sans (friendly rounded look) and a supporting sans/serif for body, self-host WOFF2 files, and adjust typography scales to convey warmth and trust.
