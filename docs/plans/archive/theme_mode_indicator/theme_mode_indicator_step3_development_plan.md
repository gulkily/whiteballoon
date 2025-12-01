# Theme Mode Indicator — Development Plan

## Stage 1 – Audit existing theme toggle
- **Goal**: Understand current markup, CSS classes, and JavaScript/state logic for the theme switcher.
- **Dependencies**: None.
- **Changes**: Read the relevant template (likely header/nav component) and associated CSS/JS to see how dark/light/auto modes are defined; note existing icon assets.
- **Verification**: Document findings in notes; no code change yet.
- **Risks**: Missing a shared component or reuse location, leading to incomplete updates later.

## Stage 2 – Design assets & states
- **Goal**: Define the split sun/moon icon and border cue styling.
- **Dependencies**: Stage 1 context on current button structure.
- **Changes**: Create SVG or CSS icon for the hybrid sun/moon, decide on dotted/dashed border treatment (ensuring contrast), and ensure accessibility labels distinguish auto mode.
- **Verification**: Preview assets locally (e.g., using story/test page) or via browser dev tools.
- **Risks**: Icon looking blurry on HiDPI or border clashing with existing layout.

## Stage 3 – Implement UI updates
- **Goal**: Wire the new icon and border state into the actual toggle.
- **Dependencies**: Stages 1-2.
- **Changes**: Update template/CSS/JS so when auto mode is active, the toggle gets the new icon and border class; ensure manual modes retain their styling. Provide appropriate `aria-label` text (e.g., “Theme: Auto (system)”).
- **Verification**: Run frontend locally, cycle through modes, visually confirm behavior and check with screen reader if possible.
- **Risks**: Regressing responsiveness or interfering with other header controls.

## Stage 4 – Polish & document
- **Goal**: Ensure code is clean, documented, and tested.
- **Dependencies**: Stage 3 implementation complete.
- **Changes**: Add brief code comments if needed, update docs/README or release notes to mention the enhanced indicator, and run lint/tests.
- **Verification**: `git status` clean besides intended files; manual smoke test again.
- **Risks**: Forgetting to capture documentation or missing edge cases on different themes.
