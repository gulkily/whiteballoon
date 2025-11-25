# Dark Mode Support — Step 2 Feature Description

## Problem
The application only offers a light theme, causing discomfort in low-light environments and ignoring user system preferences. Users need both automatic and manual control over light/dark modes.

## User Stories
- As a user, I want the site to honor my system’s dark/light preference so the UI feels comfortable immediately.
- As a user, I want a theme toggle so I can manually switch between light and dark modes regardless of system settings.
- As a returning user, I want my theme choice remembered so I don’t have to reselect it on each visit.

## Core Requirements
- Define a comprehensive dark theme palette by extending existing CSS variables (colors, shadows, borders, text).
- Detect `prefers-color-scheme` to set the initial theme automatically when no manual preference is stored.
- Add a visible toggle (e.g., in header or settings menu) allowing users to switch themes manually; persist choice in `localStorage`.
- Ensure toggle overrides system preference while session lasts and on future visits (until explicitly reset).
- Prevent flash of incorrect theme on load (apply stored preference ASAP, possibly through inline script before styles load).

## User Flow
1. User visits the site; system preference is detected and applied (unless overridden previously).
2. User optionally toggles theme; UI updates immediately while preference is stored client-side.
3. On subsequent visits, the stored manual preference takes precedence over system settings.
4. User can switch back or reset to auto mode via the same control.

## Success Criteria
- Light/dark palettes cover all components without contrast regressions (validated via manual review and contrast checks).
- Initial load respects stored preference or system setting, with no visible flash of wrong theme.
- Manual toggle updates the interface instantly and persists across sessions in the same browser.
- QA confirms theme toggling works on modern browsers and mobile devices.
