# Navbar Iconography · Step 1 Solution Assessment

**Problem statement**: The updated navbar links are text-only, so the primary row lacks visual hierarchy and doesn’t reinforce each destination, making it harder to scan at a glance.

**Option A – Inline SVG icons next to labels**
- Add a small (16px) monochrome SVG ahead of each primary nav label (Requests, Comments, Browse, Menu) and reuse the same assets on Menu page cards, bundled directly into the templates for fast render.
- Pros: Minimal dependencies, consistent across themes because we control the SVG fill, easy to adapt or swap icons.
- Cons: Requires hand-curating/maintaining icons, and the added markup marginally increases bundle size.

**Option B – Icon font (e.g., custom subset)**
- Generate a lightweight icon font (using only the 4–6 symbols we need) and reference via CSS classes across both navbar and Menu grids.
- Pros: Simplifies markup (just add a `<span class="icon-requests">`), keeps icons vector-based and easily recolorable via `currentColor`.
- Cons: Adds a build step, tricky to ensure sharp rendering on all DPI levels, and swapping icons requires regenerating the font.

**Option C – Emoji/base Unicode glyphs**
- Reuse simple glyphs (🗂️, 💬, 🔍) inline with the labels for a playful, zero-asset approach.
- Pros: No additional assets; immediate differentiation.
- Cons: Looks informal, may render inconsistently across OS/browsers, and weakens brand cohesion.

**Recommendation**: Option A. Inline SVGs give us full control over the style, respond well to theme changes, keep the DOM structure explicit, and can piggyback on the existing CSS without new tooling. We can optimize the SVGs via SVGO and reuse them across the nav, mobile panel, and Menu page for consistency.
