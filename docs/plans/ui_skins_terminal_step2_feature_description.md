# Terminal Skin — Feature Description

## Problem
We need a concrete alternative skin (green-on-black “Terminal” look) to validate the new skinning system and provide a high-contrast option for operators.

## Requirements
- Create `static/skins/terminal.css` importing `base.css`.
- Override tokens for primary colors, typography (monospace), background textures, and accent elements.
- Add any additional selectors (e.g., background gradients) to evoke a retro terminal feel while keeping layout intact.
- Ensure accessibility (contrast) and compatibility with existing components.

## Success Criteria
- `./wb skins build` produces a `skin-terminal` bundle.
- Setting `WB_SKIN_DEFAULT=terminal` renders the new aesthetic with no layout breakage.
- Documentation mentions the new skin so operators know it’s available.
