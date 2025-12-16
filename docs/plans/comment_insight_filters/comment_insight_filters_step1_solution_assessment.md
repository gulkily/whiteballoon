## Problem
The new "Comment insights" card lists resource/request tags, urgency, and sentiment across a request, but clicking those chips doesn’t show the matching comments. Users expect the chips to act as filters that reveal the relevant comments immediately.

## Option A – Full-page filter reload
- Pros: Reuse existing request detail pagination by appending `?tag=housing` (etc.) to the URL and reloading with only matching comments.
- Cons: Jarring page reload; loses scroll position; filtering by multiple tags at once gets clunky.

## Option B – Inline filtering + sharable URLs (recommended)
- Pros: Chips act as toggles that hide/show matching comments in-place, while the selected filters are synced to the URL (e.g., `?insight_tag=housing&sentiment=positive`). Users get instant feedback and can share/bookmark the state. Deep-linking into the request auto-applies the filter on load.
- Cons: Requires augmenting the comment payload/markup with tag metadata, writing client-side JS, **and** teaching the backend to parse filter params on initial load.

## Option C – Popover modal listing matches
- Pros: Clicking a chip opens a modal showing matching comment excerpts; minimal DOM churn.
- Cons: Adds a new UI surface; duplicates comment rendering; harder to navigate to the full comment context.

## Recommendation
Choose **Option B**: enrich comment serialization with the LLM tags/urgency, add client-side filtering that syncs state to query params (using History API), and honor those params server-side so shared URLs open with the same filters applied automatically.
