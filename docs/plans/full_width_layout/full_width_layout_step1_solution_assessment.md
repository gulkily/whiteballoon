# Full-width Layout · Step 1 Solution Assessment

**Problem statement**: Some pages (e.g., request feed, menu, admin screens) use the fixed-width `.container` wrapper, causing extra whitespace on large displays and inconsistent layouts between views.

**Option A – Global container tweaks**
- Adjust the base template to make `.container` stretch to the viewport width (with padding) and let every page inherit the wider canvas automatically.
- Pros: One change fixes all pages; minimal template churn; consistent gutters everywhere.
- Cons: Pages that intentionally relied on the constrained width (forms, modals) might feel too wide; requires auditing nested `.container` usage.

**Option B – Page-specific full-width wrappers**
- Leave the base container alone but add per-page overrides (e.g., `main.container.container--fluid`, custom sections) depending on content needs.
- Pros: Precise control — only broaden pages that benefit; less risk of regressing forms/dialogs.
- Cons: Requires touching many templates; easy to miss pages; long-term maintenance overhead.

**Option C – Responsive breakpoint-based expansion**
- Keep the existing container for small/medium screens but allow it to expand beyond a certain breakpoint (e.g., >1280px) using CSS media queries.
- Pros: Maintains readability on laptops while using more space on ultrawide monitors; no template changes.
- Cons: Still enforces a max width, so some designers may feel it’s not “full bleed”; requires careful breakpoint tuning.

**Recommendation**: Option A. Updating the global container to be full-width with generous side padding yields the most consistent experience and minimizes template maintenance. We can follow up with targeted adjustments (e.g., fixed-width inner cards) where true constraints are required.
