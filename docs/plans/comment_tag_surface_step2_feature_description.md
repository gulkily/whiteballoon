## Problem
LLM analyses already assign topical tags to comments, but those tags stay hidden unless an admin clicks the insights badge. Regular viewers of a request can’t see why an AI flagged it as “housing” or “urgent,” even though that context would help triage.

## User Stories
- As a member reading a request thread, I want to see the AI-derived tags/urgency summaries so I understand the conversation at a glance.
- As an admin, I want everyone to benefit from the LLM categorization without needing the privileged insight modal.
- As a moderator, I want a single place to see which tags are present across the request’s comments so I know when to escalate.

## Core Requirements
- Aggregate comment insights for a request (using `comment_llm_insights_service`) and expose the structured fields (resource/request tags, urgency counts, sentiment) to the template context.
- Render a new “Comment insights” card on the request detail page visible to any viewer who can see the request.
- The card should show top tags (grouped by type), urgency highlights, and link to `/comments/{id}` for any comment that produced a particular tag.
- Do not require extra clicks per comment; the panel should load whenever the request page loads.
- If no insights exist, hide the panel entirely.

## Shared Component Inventory
- `app/routes/ui/__init__.py` request detail context: extend to include an aggregated `comment_insights_summary` payload.
- `templates/requests/detail.html`: add a new card/section reusing existing meta-chip styles for tag display.
- `comment_llm_insights_service`: reuse the DB helper to fetch per-comment analyses and normalize tags.

## Simple User Flow
1. Request page renders; backend gathers any insights for comments on that request.
2. UI shows a “Comment insights” card listing resource tags, request tags, and urgency highlights.
3. Viewer clicks a tag label to jump to `/comments/{id}` or the related comment if desired (optional enhancement).

## Success Criteria
- Any request containing at least one analyzed comment displays the new panel automatically.
- Tags/urgency values match what the admin insight badge would show for the same comment.
- No errors or noticeable performance hits for requests without analyses.
