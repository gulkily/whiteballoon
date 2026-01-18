# Request Channels Search — Step 3 Development Plan

1. **Add search/filter params to request serialization helper**
   - **Goal**: Allow `_serialize_requests` callers (and `/api/requests`) to apply query + status filters without duplicating logic.
   - **Dependencies**: Existing `request_services.list_requests` and filter parsing helpers.
   - **Changes**: Update the helper signature to accept optional `search`, `status`, `pinned_only` flags; thread them into the DB query/service layer; ensure tests/typing updated.
   - **Verification**: Run `pytest tests/test_routes_requests.py` (or relevant module) plus a manual CLI call to `/api/requests?search=test` to confirm filtered payloads.
   - **Risks**: Performance regressions if filters bypass caching; ensure indexes exist or scope query to manageable fields.

2. **Expose enriched API response for channels**
   - **Goal**: Provide unread/comment counts alongside request payloads via the API so the workspace can refresh badges.
   - **Dependencies**: `_load_channel_comment_counts`, `request_channel_reads` services.
   - **Changes**: Extend `/api/requests` (or new endpoint) to optionally include metadata when `include_channel_meta=1` is passed; reuse the existing services to calculate counts for the returned IDs.
   - **Verification**: Manual `curl` or `httpie` call ensuring the JSON includes `comment_count`/`unread_count`; unit tests if applicable.
   - **Risks**: Additional DB queries per call; consider batching to keep latency low.

3. **Debounced remote search in Request Channels UI**
   - **Goal**: Update `static/js/request-channels.js` to fetch results from the API when search/filter parameters change, while keeping local filtering as a cache.
   - **Dependencies**: API enhancements from stages 1-2.
   - **Changes**: Add debounce utility, track last query, show a loading indicator, fetch `/api/requests?...`, rebuild the button list, and merge counts; maintain local fallback when parameters unchanged.
   - **Verification**: Manual browser test hitting `/requests/channels`, typing queries, toggling filters, confirming network requests and UI updates behave; inspect console for errors.
   - **Risks**: Race conditions between concurrent fetches; handle cancellations/out-of-order responses.

4. **Selection/presence resilience**
   - **Goal**: Ensure active channel selection, unread badges, and presence polling continue working after remote list updates.
   - **Dependencies**: Stage 3 data restructuring.
   - **Changes**: Adjust JS to keep `state.active_channel_id` even if the channel falls outside current results (maybe show a notice); refresh presence polling list; reconcile unread badges with server data.
   - **Verification**: Manual test with multiple channels—search for a subset, ensure selection persists or gracefully clears, and presence counts continue updating.
   - **Risks**: Edge cases where the active channel disappears; need clear UX (maybe default to first result).

5. **Edge-case QA + accessibility pass**
   - **Goal**: Validate empty states, debounce behavior, keyboard navigation, and ARIA attributes after the new search flow.
   - **Dependencies**: All prior stages complete.
   - **Changes**: Update templates/messages if needed (e.g., add loading text), ensure live regions announce result counts, adjust CSS for new states.
   - **Verification**: Manual QA with no results, quick toggling, keyboard navigation; optionally add Playwright/manual script.
   - **Risks**: Missing announcements could degrade accessibility; ensure search results are perceivable.
