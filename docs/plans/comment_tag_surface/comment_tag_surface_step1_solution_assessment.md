## Problem
Comment LLM analyses already store topical tags (resource/request tags, urgency, sentiment), but regular viewers never see them on comment cards; only admins can fetch them via the insights badge.

## Option A – Always show tags inline on comment cards
- Pros: Zero extra clicks; viewers read a comment and see the AI tags immediately, consistent across all lists.
- Cons: Requires loading tag data for every visible comment, adding backend queries + UI clutter; some tags may be admin-only.

## Option B – Progressive disclosure panel per comment
- Pros: Add a disclosure (e.g., “View tags”) on each comment that fetches and displays the existing insight payload on demand; keeps UI clean while remaining accessible to all roles.
- Cons: Still requires extra fetches per comment; copycat of current admin-only badge but for everyone.

## Option C – Dedicated “Insights” section per request (recommended)
- Pros: Central place (e.g., a sidebar card) that aggregates the tags for all comments on a request, so we load analyses once per request and avoid repeating chips per comment; easier to digest.
- Cons: Requires scrolling to a separate section; less granular than per-comment inline tags.

## Recommendation
Choose **Option C**. Surface the LLM tags in a single “Insights from comments” panel on each request page so everyone can browse the aggregated tags without overloading every comment card. We can expand later with per-comment expansion if needed.
