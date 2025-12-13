## Stage 1 – Insight aggregation service
- **Goal**: Collect all LLM analyses for a given request in one backend helper.
- **Dependencies**: `comment_llm_insights_service`, request detail route.
- **Changes**: Fetch comment IDs for the request (existing `request_comment_service.list_comments` data) and call `comment_llm_insights_service.get_analysis_by_comment_id` for each, accumulating unique tags/urgency counts into a lightweight summary dict.
- **Verification**: Promote or analyze a couple of comments on a test request, hit the route, and inspect/debug the summary payload.
- **Risks**: Additional queries per comment; mitigate by batching analyses from the SQLite DB or caching on the request context.

## Stage 2 – UI panel
- **Goal**: Render the aggregated tags to end users.
- **Dependencies**: Stage 1 summary payload; `templates/requests/detail.html` styling.
- **Changes**: Add a “Comment insights” card that lists resource tags, request tags, and urgency sentiment, using meta chips and optional counts; include a link to `/comments/{id}` for top contributing comments if available.
- **Verification**: Manually inspect a request with known tags; ensure panel hides entirely when summary payload is empty.
- **Risks**: Visual overload; keep layout simple and responsive.

## Stage 3 – Optional enhancements
- **Goal**: Provide quick actions such as filtering comments by tag.
- **Dependencies**: Stage 2 UI, existing comment list.
- **Changes**: If feasible, clicking a tag could scroll to or highlight related comments.
- **Verification**: Spot-check the interaction if implemented.
- **Risks**: Scope creep; skip if timeline is tight.
