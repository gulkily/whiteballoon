# Profile Comments – Step 3 Development Plan

## Stage 1 – Inline recent comment slot
- **Goal**: Render the latest N comments (configurable) on profile and Signal persona pages.
- **Dependencies**: Request comment service; profile/Signal templates.
- **Changes**: Extend profile routes/services to fetch recent comments per identity, respecting permissions/scope. Update templates to show the snippet with timestamps + request links + “View all” CTA.
- **Verification**: Load a profile with ≥N comments (native + Signal persona) and confirm the block renders the newest entries in order, respecting scope.
- **Risks**: Performance impact on large histories; missing permission filters could leak private data.

## Stage 2 – All-comments listing page
- **Goal**: Add `/people/<slug>/comments` (and Signal persona equivalent) that paginates through every comment.
- **Dependencies**: Stage 1 data plumbing; pagination helpers.
- **Changes**: New route/controller that fetches comments joined with requests, handles pagination params, and renders a dedicated template with human-friendly layout (scope badges, request links, timestamps). Add nav link/button from profile snippet.
- **Verification**: Hit the listing page for both user types, paginate through multiple pages, confirm counts/links work.
- **Risks**: Query could be slow without indexes; need to ensure unauthorized viewers are blocked.

## Stage 3 – Documentation + implementation summary update
- **Goal**: Capture the shipped behavior in Step 4 summary/README as needed.
- **Dependencies**: Prior stages complete.
- **Changes**: Update `docs/plans/...step4_implementation_summary.md` with Stage 5 details, mention snippet + listing; adjust README or admin docs if necessary.
- **Verification**: Proofread docs; ensure references are accurate.
- **Risks**: Incomplete documentation; mismatch with actual behavior.
