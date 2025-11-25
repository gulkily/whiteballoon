## Stage 1 – Comment search helpers & indexing hooks
- Dependencies: Request/comment models & services.
- Changes: Add `request_chat_search_service` that normalizes comment bodies, participant names, timestamps, and basic topic tags derived via string-matching dictionaries (e.g., "housing", "transport"). Expose functions to (a) precompute keyword tokens (lowercased text + cached participant lookup) and (b) refresh caches whenever imports or new comments land. Store caches in application memory or lightweight JSON within `storage/cache/` to avoid DB migrations.
- Verification: Manual spot-check via CLI/`signal_import` to confirm cache files populate and include topic tags; log output validating refreshes run.
- Risks: Cache invalidation bugs leading to stale search results; memory/cache footprint for very large chats; misclassified tags if keywords overlap.

## Stage 2 – Search API endpoint
- Dependencies: Stage 1 helpers.
- Changes: Add `GET /requests/{id}/chat-search` route that validates auth, reads query + optional participant/topic filters, executes Stage 1 helper, and returns matched snippets with highlight metadata + anchors. Include pagination/limit + response schema in `RequestResponse` or new Pydantic model.
- Verification: Manual API exercise via `httpie`/browser devtools ensuring empty queries, keyword searches, participant filters, and topic tags behave; confirm permission gating.
- Risks: Inefficient response payloads (large bodies), leaking comments from private requests, inconsistent highlight offsets.

## Stage 3 – UI search widget
- Dependencies: Stage 2 API, existing request detail template.
- Changes: Update `requests/detail.html` to add “Search chat” input + results pane; build small JS module to debounce input, call the new endpoint, render matches with highlighted `<mark>` tags, and support jump-to-anchor. Ensure no-JS fallback (submit triggers full reload with query params showing results server-side).
- Verification: Manual browser test on desktop/mobile; check accessibility (focus order, ARIA for results) and degrade gracefully if request lacks chat import.
- Risks: JS errors blocking comment form, layout regressions on long requests, highlight HTML introducing XSS if not escaped.

## Stage 4 – Related snippet suggestions across requests (heuristic)
- Dependencies: Stage 2 data plumbing (need tokenized text, participant metadata, topic tags).
- Changes: Add backend helper that, given a request, extracts key entities (names, emails, classified topic tags) and finds top N matches from other cached chat indices via simple overlap scoring. Surface these matches via server-rendered component or API so other request pages can show “Related chat mentions.” Hook reindex job to update suggestions when chat caches refresh.
- Verification: Manual check that viewing Request B shows suggestions referencing Request A after import and that topic tags influence ranking.
- Risks: False positives causing noise, performance impact when scanning many caches, privacy concerns if suggestions reveal private data to users without access.

## Stage 5 – Automated surfacing via embeddings (Option C)
- Dependencies: Stage 1 cache format (source text), Stage 4 suggestion plumbing (UI surface + API).
- Changes: Introduce background job (Celery-esque task or management command) that runs OpenAI/Dedalus embeddings on cached chat snippets, stores vectors in lightweight local index (e.g., FAISS or numpy dot products), and augments suggestion API to blend heuristic matches with embedding similarity. Provide admin CLI to rebuild vectors and schedule periodic refresh.
- Verification: Manual run of the embedding job against a small sample export, confirming vectors persist and blend into suggestions without blocking request handling.
- Risks: Managing external model deps within restricted environment, long-running jobs blocking process, new storage footprint, privacy review for sending chat text to embedding service.
