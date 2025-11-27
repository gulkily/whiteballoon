# Request Detail Page Polish — Step 2 Feature Description

## Problem
The request detail page still reads like a stretched feed card. Navigation, sharing, and metadata aren’t clearly organized, making the page feel like a stopgap rather than a dedicated detail experience.

## User Stories
- As a helper, I want the detail page to highlight key request context (status, author, timing) so I can quickly understand the situation.
- As a requester, I want a polished share widget so sending the link feels effortless and trustworthy.
- As a maintainer, I want space reserved for future follow-up actions (contact, tracking) without reworking the layout again.

## Core Requirements
- Break the hero into two rows: a lightweight back affordance, then the title plus concise metadata (status, requester, timestamp).
- Restyle the share widget to span the card width with a copy affordance (icon/hint) while keeping auto-select behaviour.
- Lighten and lift the request card (glass blur/inner glow) for better contrast on desktop and mobile.
- Add a footer block for “Next steps” or contact info placeholder to signal forthcoming tracking features.
- Ensure responsive spacing/typography keeps the layout balanced on small screens.

## User Flow
1. User lands on `/requests/<id>` and sees a clear back link, title, metadata, and share widget in the hero.
2. Share widget auto selects and offers visual feedback when the user taps/clicks.
3. Request card presents description/status cleanly with improved depth.
4. Footer section hints at next steps/contact actions (even if currently informational).

## Success Criteria
- Detail hero feels intentional: back link, title, metadata, and share widget aligned without crowding on desktop/mobile.
- Share widget communicates copied state visually and remains accessible.
- Request card contrast and spacing improve readability across breakpoints.
- Footer section exists, even if content is placeholder, to house future tracking actions.
- Manual smoke test on desktop + narrow viewport confirms layout integrity.
