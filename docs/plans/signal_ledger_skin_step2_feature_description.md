# Signal Ledger Skin — Step 2 Feature Description

## Problem
Current UI leans playful and mutual-aid celebratory, which makes investor demos feel less rigorous. We need a toggleable "Signal Ledger" skin that reframes the same data as a trustworthy capital-and-trust dashboard without reworking core flows.

## User stories
- As an investor guest, I want to see KPIs in a premium visual language so that the product signals operational maturity.
- As a founder host, I want to switch to the investor skin instantly so that demos stay focused on metrics instead of community storytelling.
- As an admin, I want canonical data cards to adapt automatically so that I don’t maintain separate UI variants per screen.
- As a designer, I want motion and typography guidelines documented so that future investor modules stay consistent.

## Core requirements
- Provide a selectable `Signal Ledger` theme option (URL param or UI toggle) that restyles existing pages without forked templates.
- Introduce a deep-navy/graphite palette with copper + teal accents, subdued motion, and premium typography (Inter body, editorial serif headings).
- Promote KPI hero widgets for Network Health, Capital Flows, Verification Chain, plus a sync activity timeline strip when the skin is active.
- Ensure cards, buttons, and data chips reuse canonical components with skin-specific tokens so content remains identical.
- Document motion reductions (no bounce, short fade/scale) and hover behaviors for graph edges.

### Investor theme tokens
- Base palette (WCAG AA checked on light text unless noted):
  - `sl-bg-950` #050A16 (page background, drawer rails)
  - `sl-bg-900` #0E1524 (card background default)
  - `sl-bg-800` #151C2C (timeline strip + secondary cards)
  - `sl-border-600` #24304A (1px borders/dividers)
  - `sl-accent-copper` #CE8452 (primary CTA + KPI spark lines)
  - `sl-accent-teal` #3DC9B6 (positive deltas, verification badges)
  - `sl-neutral-200` #C8D2E6 (muted labels)
  - `sl-neutral-50` #F4F7FF (on-dark text)
- Token mapping:
  - Cards use `sl-bg-900` with `sl-border-600`; hover lifts swap to `sl-bg-800`.
  - Buttons reuse `btn` classes with CSS vars: `--btn-bg` defaults to `sl-accent-copper`, `--btn-text` to `sl-neutral-50`.
  - Identity chips keep size but swap background to transparent, border to `sl-accent-teal`, text `sl-neutral-50`.

### KPI hero + layout guidance
- Inject hero row right below top navigation; 12-column grid with gutter 24px.
- Card sizing:
  - Network Health: spans 5 columns, height 220px, includes gauge + % delta.
  - Capital Flows: spans 4 columns, height 220px, stacked bar trendline.
  - Verification Chain: spans 3 columns, height 220px, stepper list.
- All three reuse dashboard metric component with `themeVariant="investor-hero"` prop to trigger condensed padding (24px) and serif heading override already defined globally.
- Data API: same fields as existing dashboard metrics; no new endpoints required. If metric data missing, show skeleton shimmer (88ms fade) but reserve layout slot to avoid content shift.

### Sync activity timeline strip
- Appears directly under hero row, full width, background `sl-bg-800`, 56px height.
- Component reuse: existing timeline list rendered horizontally; each entry condenses to timestamp + verb + entity chip. Overflow scrolls horizontally (momentum disabled per motion guidance).
- Data limit: latest 8 events; if fewer, keep empty slots with dotted border.
- Loading: shimmer placeholders matching entry width (120px) with 120ms fade.

### Motion + hover tokens
- Global easing `cubic-bezier(0.2, 0.8, 0.2, 1)` with durations capped at 160ms. Entrance animations use fade+2px scale from 98%.
- Hover states on graph edges/links: opacity shift from 60% to 90% over 120ms; no translate/bounce.
- Timeline auto-scroll disabled; manual scroll decelerates immediately when user lifts (feels controlled).
- Focus outlines reinforced with `sl-accent-teal` 2px ring to keep accessibility despite dark palette.

### Accessibility validation
- Contrast references logged in theme sheet; min 7.6:1 for `sl-neutral-50` text on `sl-bg-900`, 4.8:1 for muted labels on `sl-bg-800` (above AA for large text used there).
- KPI spark lines maintain 3px stroke so copper on navy meets non-text contrast guidance.
- Identity chips rely on outline rather than fill to keep accessible surface area while minimizing saturation.

## Shared component inventory
- Request cards → reuse existing card markup; extend theme tokens for background, borders, and typography weight.
- Identity chips → reuse canonical component with palette swap only; no structural change.
- KPI widgets (Network Health, Capital Flows, Verification Chain) → extend existing dashboard metric component; add investor-specific layout variant via theme props.
- Sync activity log entries → reuse current timeline list and add condensed styling; no new data fields.
- Buttons + toggles → reuse `btn` classes with investor palette tokens; avoid new button classes.

## User flow
1. Admin or host opens dashboard and selects the `Signal Ledger` skin toggle (or appends `?skin=investor`).
2. Theme engine loads the investor token set (color, typography, motion constraints).
3. Existing components re-render with investor styling: navigation rail appears, hero widgets surface KPI metrics, timeline strip aligns beneath hero.
4. Host conducts investor walkthrough; optional revert to default skin via toggle for community-focused view.

## Success criteria
- Toggle applies across dashboard, requests feed, members, and admin panels without template duplication.
- KPI hero widgets and timeline load within 200ms of theme switch (no layout thrash).
- All canonical components pass accessibility checks (contrast ≥ WCAG AA) under the new palette.
- Demo hosts report investor skin readiness (qualitative) and no more than 1 follow-up styling issue after first demo cycle.
