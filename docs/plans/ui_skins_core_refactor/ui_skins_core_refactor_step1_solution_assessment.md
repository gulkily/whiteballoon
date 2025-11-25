# UI Skins Core Refactor — Step 1 Solution Assessment

## Problem
To support multi-bundle skins, we must first extract shared utilities/layout/color tokens from the monolithic `app.css`. We need a maintainable way to ensure every component derives from a common token set so future skins override cleanly without duplication.

## Option A – Gradual token sweep inside existing app.css
- **Pros**: Minimal file churn; developers replace literals in place while keeping single build.
- **Cons**: Hard to verify coverage; default skin logic stays entangled with base styles; future bundles still coupled to monolith.

## Option B – Create `skins/base.css` partial + retrofit components
- **Pros**: Establishes explicit base layer consumed by every skin bundle; clarifies ownership of utilities vs theme overrides; enables automated checks (import order, token definitions).
- **Cons**: Requires moving large chunks of CSS, risk of regression during migration; needs updated build pipeline soon after.

## Option C – Tokenize via CSS custom properties only
- **Pros**: Lowest structural change; can continue shipping single CSS while prepping for bundles later; leverages existing `:root` definitions.
- **Cons**: Doesn’t solve multi-bundle need; layout/typography differences still difficult; Terminal/Win95 skins limited to palette swaps.

## Recommendation
Adopt **Option B**. Creating a dedicated `skins/base.css` (or SCSS) partial and retrofitting components to consume shared tokens provides the cleanest foundation for later bundles. Although it requires more upfront movement, it directly supports the multi-bundle pipeline envisioned in the complex plan and keeps Default skin separated from the base infrastructure.
