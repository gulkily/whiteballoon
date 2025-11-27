# Comment Card Alignment – Step 3 Development Plan

## Stage 1 – Canonical partial + template
- **Goal**: Finalize `comment_card.html` variants (request/profile/search) and rewire request + profile views to use them without altering legacy styling.
- **Changes**: Keep request markup identical to pre-refactor layout, add optional slots for actions, ensure profile/search variants handle display names, timestamps, and scope consistently. Document expected parameters.
- **Verification**: Load request detail + profile pages; confirm design matches previous state.

## Stage 2 – Chat search (server + JS)
- **Goal**: Ensure chat search fallback and JS-driven results render the same card.
- **Changes**: Server: rework fallback loop to build `comment_card` input data; API: return `display_name` + `comment_anchor`. Client: rebuild `request-chat-search.js` to clone a `<template>` that matches the partial instead of hand-rolling markup.
- **Verification**: Hit `/requests/<id>?chat_q=foo` (no JS) and the inline search (with JS) plus `/requests/<id>/chat-search?q=foo` JSON to confirm identical identity/timestamp display.

## Stage 3 – Clean docs + summary
- **Goal**: Document the new shared component and update the Step 4 summary.
- **Changes**: Add a short note in the README or contributor docs about using `comment_card.html`, update `comment_card_alignment_step4_implementation_summary.md` once done.
- **Verification**: Cross-check docs for accuracy; run through the manual checklist one more time.
