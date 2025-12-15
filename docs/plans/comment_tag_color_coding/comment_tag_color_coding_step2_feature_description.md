# Comment Tag Color Coding · Step 2 Feature Description

**Problem**: Resource and request insight tags render with identical neutral styling, so reviewers can’t quickly distinguish between offers vs. asks or spot repeated tags across the request, comment, and admin surfaces.

**User stories**
- As an operator reviewing a busy request thread, I want color cues for each tag so I can skim which needs or resources are recurring without reading every chip label.
- As a moderator deciding whether to promote a comment, I want the promoted-comment insight chips to retain their colors so I trust the AI tags that justified the promotion.
- As an admin browsing comment insights in the dashboard, I want consistent tag colors between the inline badges and the comment detail modal so I can rely on muscle memory.

**Core requirements**
1. Derive a deterministic hue for every resource/request tag slug (hash → hue 0–359) and expose the hue to templates/API payloads.
2. Extend the shared `meta-chip` presentation so chips with a tag hue set CSS custom properties (hue plus theme-specific saturation/lightness) instead of hard-coded colors.
3. Surface colorized chips anywhere resource/request tags appear today: comment detail, request insight summary, promoted comment cards, admin insight badges, and any JSON the JS badge loader consumes.
4. Ensure colors remain accessible in every active skin (base/dark/etc.) via theme overrides for saturation/lightness/text color.
5. Provide a graceful fallback (neutral chip) when a hue is missing or hashing fails so we never render invisible chips.

**Shared component inventory**
- `templates/partials/comment_card.html` + `meta-chip` styles: base chip component that already standardizes size/spacing; we extend it with hue-driven variants rather than duplicating markup.
- `templates/comments/detail.html`, `templates/requests/detail.html`, `templates/partials/promoted_comment_card.html`, `static/js/comment-insight-badges.js`: all reuse the chip component to show insight tags; each must receive the hue metadata so they can apply the same CSS class/data attribute.
- Admin insights API (`/api/admin/comment-insights/...` via `comment_insight_badges.js`): needs to emit the hue value alongside `resource_tags`/`request_tags` so the client render matches server-rendered chips.

**User flow**
1. Operator opens a request detail page and sees the AI insight summary; each resource/request chip displays with its computed color (consistent across the page).
2. Operator scrolls through the comments; every inline tag chip uses the same color as in the summary, making duplicates easy to spot.
3. If they open a comment permalink or promoted-comment card, the same hues reinforce the tag meaning; admin dashboards and JS-loaded popovers reuse the identical hue, so the experience stays consistent across surfaces.

**Success criteria**
- At least 95% of requests/comments with resource/request tags display colored chips with deterministic, repeatable hues across all surfaces.
- Visual QA on each active skin confirms WCAG AA contrast for chip text/borders using the new CSS variables.
- No regressions in tag rendering: missing metadata falls back to the neutral chip style, and JS-loaded badges match the server-rendered hues.
