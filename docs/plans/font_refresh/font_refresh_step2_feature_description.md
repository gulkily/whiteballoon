# Font Refresh — Step 2 Feature Description

## Problem
System fonts make the UI feel generic; we want typography that reflects warmth and community while staying fully self-hosted (no third-party requests).

## User Stories
- As a visitor, I want headings that feel welcoming and distinctive.
- As a reader, I want body text that’s easy on the eyes across devices.
- As a maintainer, I want fonts self-hosted (WOFF2) with minimal performance impact.

## Core Requirements
- Select two open-source fonts (e.g., friendly rounded sans for headings, clean sans for body) and bundle WOFF2 files locally.
- Update CSS to load fonts with `@font-face`, including fallbacks and `font-display: swap`.
- Adjust typography scale (font sizes, weights, line heights) to enhance readability and align with mutual-aid tone.
- Ensure dark/light mode legibility and maintain accessibility contrast.
- Document font choices and where files live.

## User Flow
1. Page loads using font-face definitions (swap ensures content appears quickly).
2. Headings and UI elements use new display font; body uses secondary font.
3. Fallback stack remains graceful if custom fonts fail to load.

## Success Criteria
- Fonts load locally; no network requests to external CDNs.
- Typography feels distinctive and readable; headings yield immediate brand recognition.
- Performance impact minimal (WOFF2, swap strategy); verified via browser dev tools.
- README/CSS comments document font provenance and instructions.
