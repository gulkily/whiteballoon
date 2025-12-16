# Comment Tag Color Coding · Step 1 Solution Assessment

**Problem statement**: Resource and request insight tags currently share the same neutral styling, so reviewers can’t distinguish offers vs. needs—nor individual tags—at a glance.

**Option A – Category-based chip variants**
- Add lightweight CSS variants (e.g., `.meta-chip--resource`, `.meta-chip--request`) on top of the existing `meta-chip` component and apply them to every resource/request tag render (comment detail, promoted cards, summaries, admin badges).
- Reuse the current design tokens so both variants meet contrast guidelines without introducing new utility classes or inline styles.
- Pros: minimal template churn (just add classes), consistent palette across the product, no JavaScript, easy to extend to future contexts, accessible because styles live in the shared skin.
- Cons: all resource tags share one color and all request tags share another, so there’s no per-tag differentiation; still ambiguous when several tags are listed together.

**Option B – Deterministic per-tag hues**
- Hash each tag slug to a hue (e.g., `hue = md5(slug) % 360`), emit the hue (or computed color) with the serialized insight metadata, and let each skin set saturation/lightness via CSS custom properties so accessibility stays theme-aware.
- Server computes the color once (Jinja, admin JSON, etc.) so JS consumers simply render the provided value—no duplicated algorithms—while skins override `--tag-saturation`/`--tag-lightness` for their palette.
- Pros: automatically yields unique, repeatable colors for every tag, zero maintenance for new slugs, and keeps theme knobs localized to CSS; future analytics legends can reuse the same hues.
- Cons: slightly more plumbing (store hue/color alongside tags), needs QA to ensure hashed hues remain distinguishable and meet contrast ratios, and we must guard against sudden palette shifts if the hashing logic changes.

**Recommendation**: Option B. The requirement has grown to unique colors per tag, and deterministic hues give us that with predictable output, no registry upkeep, and skin-level control over contrast. We still reuse the meta-chip component—just augment it with color variables—so the implementation remains manageable while meeting the new visual goal.
