# Background & Motion Finishing Pass — Step 2 Feature Description

## Problem
Our gradients and floating bubbles vary per page; mid-feed scrolls feel flat and some screens show banding. Motion cadence isn’t consistent, so the brand ambiance shifts rather than staying cohesive.

## User Stories
- As a visitor, I want backgrounds that feel consistent between feed, detail, and aux pages so the brand vibe carries through.
- As a motion-sensitive user, I want subtle, predictable animation that respects `prefers-reduced-motion`.
- As a maintainer, I want a small set of gradient/motion tokens that are easy to tweak without touching every page.

## Core Requirements
- Define shared gradient/motion tokens (color stops, opacity, animation duration) and apply them across layouts.
- Adjust bubble overlays to avoid mid-page dead zones and reduce banding on large monitors.
- Ensure reduced-motion preference disables animation but keeps visual richness.
- Verify contrast/legibility with new colors in both light and dark themes.

## User Flow
1. User navigates from feed to detail to invite page and sees cohesive gradients/bubbles.
2. Motion plays smoothly; on reduced-motion, backgrounds stay static but attractive.
3. No hot spots or banding during long scrolls.

## Success Criteria
- Gradient tokens defined in CSS and reused across pages.
- Animation timing consistent; bubble placement covers entire viewport without clutter.
- Manual checks confirm no banding artifacts, adequate contrast, and `prefers-reduced-motion` compliance.
