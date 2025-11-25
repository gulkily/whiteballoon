## Problem
We need a clear way for members to visualize the invite network so they can see 1st-, 2nd-, and 3rd-degree connections and understand who invited whom.

## Options
- **Server-rendered tree view (HTML/CSS)**
  - Pros: Minimal JS, fits current stack, easy to link directly, SEO-friendly, quick to implement.
  - Cons: Limited interactivity, harder to collapse/expand large branches, layout may be tight on mobile.
- **Client-rendered interactive tree (lightweight JS)**
  - Pros: Smooth expand/collapse, easier highlighting of degree levels, better for growing networks.
  - Cons: Requires new JS utilities, added complexity/testing, more error-prone on older browsers.
- **Visualization with external library (e.g., D3.js or Cytoscape)**
  - Pros: Rich layouts, automatic spacing for large graphs, built-in interactions.
  - Cons: Heavy dependencies, steeper learning/testing curve, likely overkill for ≤3 degrees.

## Recommendation
Pursue the server-rendered tree view. It honors the 3-degree requirement with minimal new tooling, keeps maintenance low, and we can still add simple CSS/JS enhancements later if usage grows.
