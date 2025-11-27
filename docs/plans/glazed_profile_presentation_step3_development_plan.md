# Glazed Profile Presentation – Step 3 Development Plan

## Stage 1 – API wiring + feature flag
- **Goal**: Plumb highlight data into profile routes safely.
- **Dependencies**: Highlight service (Capability 3), existing `/profile` + `/admin/profiles` handlers.
- **Changes**: Extend FastAPI dependencies to fetch `Highlight` + snapshot stats when `PROFILE_SIGNAL_GLAZE` flag enabled. Ensure caching to avoid N+1 queries. Document new context keys.
- **Verification**: Unit tests verifying context includes highlight only when flag on.
- **Risks**: Performance regressions; mitigate with caching + minimal queries.

## Stage 2 – Member-facing card
- **Goal**: Render celebratory bios for authenticated members.
- **Dependencies**: Stage 1 context.
- **Changes**: Update `templates/profile/show.html` with “Community perception” card: bio paragraphs, proof-point pills linking to requests/URLs, freshness chip, fallback text if highlight missing. Ensure markup reuses existing card styles.
- **Verification**: Template tests + manual UI review (desktop/mobile).
- **Risks**: Accessibility (screen readers); rely on semantic headings + aria labels.

## Stage 3 – Admin controls panel
- **Goal**: Surface provenance + controls to operators.
- **Dependencies**: Highlight data + admin routes.
- **Changes**: In `templates/admin/profile_detail.html`, add panel summarizing highlight text, staleness, provenance metadata, plus buttons to “Regenerate via CLI” (POST to backend) and “Lock manual copy”. Include explanatory microcopy.
- **Verification**: Manual admin QA; ensure CSRF tokens + permission checks.
- **Risks**: Trigger spam; add rate limit or confirmation dialog.

## Stage 4 – Receipts links & analytics
- **Goal**: Provide verifiable links and measure engagement.
- **Dependencies**: Snapshot data (top links/request IDs), instrumentation framework.
- **Changes**: Helper to format `top_links` into outbound anchors with domain labels. Add CTA chips linking to request comments filtered for the user. Instrument client-side click + view events (POST to `/api/metrics`).
- **Verification**: Unit tests for helper; manual check that analytics fire (inspect network requests).
- **Risks**: External links may be unsafe; ensure `rel="noopener noreferrer"` and basic URL validation.

## Stage 5 – Permission hardening & fallbacks
- **Goal**: Guarantee Signal-derived data only visible to allowed audiences and degrade gracefully.
- **Dependencies**: Stages 1–4.
- **Changes**: Enforce checks so only signed-in members/admins can see glaze block; others see standard profile. Add fallback messaging when highlight stale/missing. Document behavior in `docs/features/profile_signal_glaze.md`.
- **Verification**: Permission tests covering guest/member/admin scenarios.
- **Risks**: Data leakage; mitigate via explicit guards + regression tests.
