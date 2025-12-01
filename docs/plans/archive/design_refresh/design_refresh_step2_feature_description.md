# Design Refresh — Step 2 Feature Description

## Problem
The current interface feels static and muted. We want a lively aesthetic—moving background, colorful bubbles, celebratory elements—while clearly communicating the warmth, trust, and solidarity of our mutual-aid community (without adding new dependencies or major architectural changes).

## User Stories
- As a visitor, I want a vibrant, animated backdrop that suggests community motion and togetherness.
- As a member, I want interface elements (cards, buttons) to feel playful, welcoming, and clearly tied to mutual support.
- As an admin, I want the design refresh to be maintainable and minimal (no new frameworks), relying on CSS/JS tweaks.

## Core Requirements
- Implement a lightweight animated background (e.g., CSS gradients or small JS loop) with minimal CPU impact.
- Introduce floating/bubbly UI accents (e.g., layered divs, subtle animations) to sections like headers and mutual-aid request cards.
- Ensure readability and accessibility (contrast, motion controls, respect reduced-motion settings).
- Keep changes minimal: pure CSS/vanilla JS additions; no new dependencies.
- Update the home/dashboard templates with celebratory bubbles/confetti touches.

## User Flow
1. Visitor lands on home/dashboard; background animates softly, floating accents appear.
2. Cards/buttons use updated palette and shapes (rounded “bubbles”).
3. Reduced-motion users see toned-down or static variants via media query.

## Success Criteria
- Animated background runs smoothly on modern browsers; motion respects `prefers-reduced-motion`.
- UI elements adopt colorful, semi-transparent bubble style while preserving readability.
- No new dependencies are introduced; documented CSS/JS easily maintainable.
