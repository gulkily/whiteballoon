# Break In Skin · Step 3 Development Plan

## Stage 0 – Reference capture & asset prep
- **Goal**: Translate the screenshot (Break In landing page) into concrete assets and constraints before touching CSS.
- **Changes**: Export the Bay Bridge night photo (1920×1080 min) with a subtle gaussian blur and store it under `static/img/skins/break-in/hero.jpg`. Capture the neon gradient used behind “BREAK IN” (lime → transparent over dark navy) plus the tiny uppercase eyebrow text treatment. Decide on two display fonts: `Space Grotesk` for the neon titles and `Inter` fallback for body. Note CTA button shapes (pill, 2px white border) and sponsor lockups (JPMorgan, Insight, etc.) for later placement.
- **Verification**: Save a short reference sheet (PNG or PDF) alongside the image and ensure licensing/attribution is documented in `docs/skins/README.md` (if new assets require it).

## Stage 1 – Define Break In token set
- **Goal**: Add a new skin bundle `static/skins/break-in.css` that imports `./base.css` and establishes the neon palette + typography tokens.
- **Changes**:
  - Light mode (used sparingly) still leans dark: `--color-surface: #030617`, `--color-card: rgba(5, 12, 32, 0.92)`, `--color-text: #f4f8ff`, `--color-muted: #7e8fab`.
  - Accents: `--color-accent: #d8ff3f` (electric lime), `--color-accent-strong: #f6ff6f`, `--color-info: #37c1ff` (for CTA outlines), `--color-warning: #ffe169`.
  - Background gradients: `--skin-background-gradient: linear-gradient(180deg, rgba(6, 11, 29, 0.88), rgba(3, 4, 12, 0.95)), radial-gradient(circle at 20% 20%, rgba(216, 255, 63, 0.18), transparent 60%)`, plus a hero image overlay applied to `.page-wrap::before`.
  - Typography: add `--font-heading: 'Space Grotesk', 'Chakra Petch', var(--font-heading); --font-body: 'Inter', 'Space Grotesk', system-ui;` plus tighter heading line height (`--line-height-heading: 1.05`).
  - Tokenize CTA + pill styles (`--skin-button-bg`, `--skin-button-ghost-border`, etc.) to mimic the glassy neon buttons, and define custom status chips (`--color-status-open-bg = rgba(216,255,63,0.12)`, etc.).
- **Verification**: Run `./wb skins list` to confirm the new file is registered. Manually load `/?skin=break-in` with preview enabled and check that the base palettes flip without overriding layout rules.

## Stage 2 – Hero treatment (background + headline)
- **Goal**: Recreate the top hero with the bridge photography, dual “BREAK / IN” headline, and program metadata.
- **Changes**:
  - Update the hero wrapper (`.home-hero` or `.requests-hero` depending on page) with pseudo-element overlays referencing the new `hero.jpg` and gradient mask. Keep the asset path relative: `background-image: linear-gradient(...) , url('/static/img/skins/break-in/hero.jpg');`.
  - Add CSS hooks for `.hero__split-headline` that renders two block spans with neon glow (`text-shadow: 0 0 45px rgba(216,255,63,0.6)`), large uppercase (clamp between 48–96px), and letter-spacing 0.06em. Provide `data-heading-left` / `data-heading-right` attributes to keep text manageable from templates.
  - Eyebrow metadata (date, city) should reuse existing `.hero__meta` markup but adopt condensed uppercase styling: `font-size: 0.75rem`, `letter-spacing: 0.25em`, muted slate color.
- **Verification**: Capture a screenshot showing the hero text legibility over the bridge image on desktop and mobile widths. Confirm Core Web Vitals (CLS) unaffected by background load (use `background-size: cover` + `min-height: 80vh`).

## Stage 3 – CTA cluster & founder callouts
- **Goal**: Mirror the centered CTA buttons and the two small callout blocks (“Call up founders…”, “Bring into the city…”).
- **Changes**:
  - Extend button utility classes so `.btn-primary` in this skin is transparent with neon border (`border: 2px solid #ffffff`, `background: rgba(255,255,255,0.05)`, `backdrop-filter: blur(6px)`), while `.btn-secondary` inherits the lime fill. Add hover states that invert fill vs. outline.
  - Use CSS grid inside `.hero__cta` to place two buttons (Sign Up for Updates + LinkedIn) stacked on mobile and inline on desktop. Include small uppercase captions under each with `font-size: 0.7rem`.
  - For the callouts, reuse info-card components but override backgrounds to `rgba(2, 4, 18, 0.86)`, add 1px lime border, drop shadow `0 0 20px rgba(216,255,63,0.25)`, and align text left with uppercase headings.
- **Verification**: Run through keyboard focus order to ensure both buttons remain accessible. Validate color contrast (lime text on near-black >= 7:1).

## Stage 4 – Sponsor row + “Program Details” body section
- **Goal**: Style the mid-page sponsor strip and program narrative block (dark navy section with bold headline).
- **Changes**:
  - Insert a sponsor container after hero using existing `.supporters` partial; set background to `#02040f`, add a thin lime top border, and center logos with grayscale filter until hover.
  - For the Program Details block, adjust the section background to `#081229`, add generous padding, and enforce `max-width: 960px` centered text. Headings use `Space Grotesk` uppercase, while paragraphs maintain 20px line height. Add a subtle gradient divider before/after the heading to match screenshot.
  - Implement `blockquote`-style emphasis for key sentences using `border-left: 4px solid rgba(216,255,63,0.45)` and italicized text.
- **Verification**: Compose a Markdown-to-HTML test snippet (existing templates render Jinja content) to ensure text sizes follow the new rules without affecting other skins.

## Stage 5 – Subscribe form + footer finish
- **Goal**: Build the “Stay Updated” form reminiscent of the screenshot (pill input boxes on dark navy background).
- **Changes**:
  - Create a `.break-in-form` component that stacks label text, two inputs (email + phone), and a CTA button. Inputs use translucent background (`rgba(255,255,255,0.04)`), 1px border `rgba(255,255,255,0.35)`, uppercase placeholders, and 50px border radius. Button inherits neon fill with drop shadow.
  - Footer rows should darken to `#050710`, include uppercase “Follow us” text, and adopt minimal icons (LinkedIn/Twitter) using neon hover states.
  - Ensure the new component respects existing form validations; only CSS overrides should be necessary, but allow template injection for the `Stay Updated` heading if not present.
- **Verification**: Trigger form validation errors to confirm red states are legible (use `--color-danger: #ff5c5c` on dark background). Test mobile breakpoints to keep inputs full-width.

## Stage 6 – QA + skin manifest
- **Goal**: Ship the skin as a selectable option with reproducible build artifacts.
- **Changes**:
  - Add `break-in` to `WB_SKINS_ALLOWED` in `.env.example` (commented) and update documentation on how to preview (`?skin=break-in`). Ensure `tools/skins_build.py` picks up the new file and `static/build/skins/manifest.json` includes it.
  - Run manual regression across core surfaces (requests feed, member cards, admin tables) to verify tokens don’t break data density views. Pay attention to table zebra striping and timeline badges—override if lime accent becomes distracting.
  - Capture before/after screenshots and log them in `docs/plans/archive/ui_skins_break_in/` once implemented.
- **Verification**: `./wb skins build && pytest tests/test_skins.py` (if present) should pass; load the Hub, Requests, Members, and Admin areas with the new skin and record issues before closing the plan.

