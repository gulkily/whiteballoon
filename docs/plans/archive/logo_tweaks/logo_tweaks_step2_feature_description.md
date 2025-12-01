# Logo Tweaks — Step 2 Feature Description

## Problem
Our text-only logotype feels generic and doesn’t visually communicate the uplifting, mutual-aid nature of WhiteBalloon.

## User Stories
- As a visitor, I want the logo to instantly convey a caring, uplifting community.
- As a returning member, I want a recognizable icon that works in navigation, favicon, and invite links.
- As a maintainer, I want the implementation lightweight (SVG/CSS) with accessible colors.

## Core Requirements
- Design a small balloon-heart icon that can sit to the left of the wordmark in the nav.
- Provide CSS/SVG styling that supports light/dark modes.
- Ensure the wordmark typography is consistent with the new visual refresh.
- Include alternative asset for favicon/social previews.
- Document usage (e.g., in README or a branding note).

## User Flow
1. Logo appears in nav and on invite page header.
2. Hover/focus states give subtle glow consistent with design refresh.
3. Favicon uses same icon for recognition.

## Success Criteria
- Icon renders clearly at 24px–48px sizes.
- Logo adapts to dark/light backgrounds without readability issues.
- No additional dependencies; assets manageable within repo.
