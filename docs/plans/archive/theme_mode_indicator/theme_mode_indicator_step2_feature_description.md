# Theme Mode Indicator — Feature Description

## Problem
When users click the dark/light toggle while the UI is in "auto" mode, the theme might not change immediately (because the OS preference already matches), leaving no visual cue that they just switched modes; the button gives no feedback showing whether it's in auto or manual state.

## User Stories
- As a visitor, I want the theme switcher to show when it's following my system preference so I understand why the appearance didn’t change after I clicked.
- As a tester, I want the control to clearly differentiate manual dark/light selections versus auto mode so I can quickly verify behavior.
- As a developer, I want an unobtrusive indicator that communicates auto mode without adding text clutter to the header.

## Core Requirements
- Add a distinct visual state to the theme toggle when auto mode is active combining a split sun/moon icon and a dotted (or otherwise unique) border cue, without altering existing layout dimensions.
- Ensure the indicator is accessible (meets contrast guidelines and is announced to screen readers if necessary).
- Preserve existing manual dark/light states and their current appearance/behavior.

## User Flow
1. User clicks the theme toggle while in manual dark or light mode; button updates as it does today.
2. User cycles into auto mode; button swaps to the hybrid sun/moon icon, shows the special border, and the change is obvious even if the page theme stays the same.
3. Leaving auto mode removes the indicator and the UI reflects the selected theme.

## Success Criteria
- Clicking the toggle into auto mode provides immediate visual feedback distinct from dark/light states.
- Manual states remain visually unchanged, and switching themes still works.
- Indicator meets accessibility expectations (contrast, screen reader text) and behaves correctly across responsive breakpoints.
