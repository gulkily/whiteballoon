# Chat Reaction Rendering – Step 1: Solution Assessment

**Problem statement**: Signal-imported chat messages currently embed raw “(Reactions: …)” text (e.g., “(Reactions: Luca ❤️, emil ❤️, …)”) inside the body, which clutters the transcript and makes reactions hard to scan.

## Option A – Parse and render reactions as structured UI
- **Pros**: Keeps message text clean while still surfacing every reaction; easy to extend with interactive chips later.
- **Cons**: Requires parsing plus new UI elements; more effort than a quick cleanup.

## Option B – Collapse reactions into summary text (recommended)
- **Pros**: Minimum viable change—detect the “(Reactions: …)” suffix, remove it from the body, and display a concise summary such as “Reactions: ❤️ ×12”; keeps the transcript tidy without complex UI.
- **Cons**: Drops the per-person detail from signal imports; summary still lives in text form (albeit cleaner).

## Recommendation
Pursue **Option B** as the fast cleanup: strip the verbose reaction list from message bodies and show a short summary line (possibly with emoji counts). This declutters the view immediately, and we can revisit Option A later if we need richer interaction.
