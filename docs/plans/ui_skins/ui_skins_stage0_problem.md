# UI Skins — Stage 0 Problem Framing

## Problem Statement
Instance operators want to offer multiple branded UI skins/themes to their community, but the frontend currently supports only a single light/dark palette with limited customization. Developers lack a structured way to add or swap skins without risking regressions or forking CSS.

## Current Pain Points
- Operators resort to ad-hoc CSS overrides that are hard to maintain across updates.
- The existing theme toggle only cycles auto/light/dark and cannot reference branded variations (e.g., "Midnight", "Solarized").
- Designers have no sandboxed workflow to build/test alternative skins before deployment.

## Success Metrics
- Operators can enable at least 3 distinct skins via configuration without editing core CSS.
- Developers can scaffold a new skin in ≤30 minutes, with preview support in the dev server.
- 0 regressions in existing light/dark behavior when no extra skins are configured.

## Guardrails
- Avoid introducing per-user persisted skins in this scope (instance-wide selection only).
- Reuse current theme preference infrastructure where possible; no new backend storage unless essential.
- Keep bundle size impact minimal (<10% CSS growth) and ensure skins share base components to avoid duplication.
