# Comment & Request Indexing Reference

This guide explains every backend mechanism we currently have for persisting, indexing, and processing comments and requests. Use it as a map when you need to figure out where a given feature gets its data or how to regenerate a cache.

## Canonical Data Stores

- **Requests** live in the `help_requests` table and are managed by `app/modules/requests/services.py`. Requests can be created directly (`create_request`) or indirectly via comment promotion (see below).
- **Comments** live in `request_comments` and are managed by `app/services/request_comment_service.py`, which enforces validation, pagination, and serialization rules used across the UI.
- **Comment attributes/promotions** use `comment_attributes` / `comment_promotions` and provide the metadata hooks needed for background pipelines (promotion queue, insights badges, etc.).

Everything else in this document builds on top of these tables.

## Request Chat Search Index

- **Module:** `app/services/request_chat_search_service.py`
- **What it does:** Turns every comment in a specific request into a `ChatSearchIndex` containing normalized text, token sets, heuristic topics, optional AI topics, and participant lookup tables.
- **How it runs:** The CLI entry point is `wb chat index` (implemented by `app/tools/request_chat_index.py`). You can target particular requests (`wb chat index --request-id 42`) or sweep everything with `--all`. Passing `--llm` enables Dedalus-powered topic labeling; scopes such as `--llm-comment`, `--llm-latest`, and `--llm-all` control which comments are sent to the classifier.
- **Cache format:** Each run writes `storage/cache/request_chats/request_<id>.json`, which contains the serialized index plus metadata such as generation timestamp and per-user participant tokens.
- **Consumers:**
  - `/requests/{id}` loads the index to power faceted chat search (`chat_q`, `chat_topic`, `chat_participant` query params) via `_build_request_detail_context`.
  - `/requests/{id}/chat-search` streams JSON search results by calling `search_chat(...)` directly.
  - `wb chat embed` (below) reuses the cached entries as its source of comment text.
  - `request_chat_suggestions.suggest_related_requests` uses the cached entries to compute overlap scores.
- **Observability:** Dedalus classifier invocations are wrapped with `app/dedalus/logging` so LLM usage appears inside `/admin/dedalus/logs`.

## Request Chat Embedding Index

- **Module:** `app/services/request_chat_embeddings.py`
- **What it does:** Stores cosine-friendly embedding vectors for a slice of recent comments on each request, plus an aggregate vector used for similarity comparisons.
- **How it runs:** `wb chat embed` (`app/tools/request_chat_embeddings.py`) loads the latest chat index for each selected request, picks the newest `N` comments (`--max-comments`, default 40), batches them, and sends them to either:
  - `DedalusEmbeddingAdapter` (default) for actual embeddings (`text-embedding-3-large`), or
  - `LocalEmbeddingAdapter` for deterministic hashed vectors during development/tests.
- **Cache format:** Persisted as `storage/cache/request_chat_embeddings/request_<id>.json` containing the model name, timestamp, individual comment vectors (with precomputed norms), and aggregate vector.
- **Consumers:** `request_chat_suggestions` (below) compares aggregate vectors, and any new semantic features should load the same cache through `request_chat_embeddings.load_index`.

## Related-Request Suggestions

- **Module:** `app/services/request_chat_suggestions.py`
- **What it does:** Scans every cached chat index + embedding index to find other requests that look related to the current one via topic overlap, participant overlap, and optional embedding similarity.
- **Inputs:** Requires a current `ChatSearchIndex` (ensured via `ensure_chat_index`) and attempts to pair it with cached embeddings for both the current request and potential matches.
- **Scoring:** Base score combines `topic_overlap * 1.5 + participant_overlap`. If embeddings exist and cosine similarity crosses `EMBEDDING_ONLY_MIN_SIMILARITY`, the request can be suggested even without keyword overlap.
- **Output:** Returns decorated payloads with snippet anchors used by the request detail page (see `_build_request_detail_context` around line 1926). This is what powers the “Related chat mentions” sidebar.

## Comment LLM Insights Pipeline

- **Module:** `app/tools/comment_llm_processing.py`
- **Command:** `wb comment-llm [opts]`
- **Purpose:** Batch comments through an LLM rubric to capture summaries, resource/request tags, urgency, sentiment, and other metadata; persist those insights; optionally enqueue request-like comments for follow-up.
- **How it selects comments:** `CommentBatchPlanner` can filter by ID ranges, user IDs, request IDs, created_at windows, inclusion of deleted comments, etc. Use flags like `--limit`, `--user-id`, `--help-request-id`, `--min-id`, `--resume-after-id`, etc.
- **Execution flow:**
  1. Plan batches and print cost estimates (token counts and USD) using `DEFAULT_MODEL` (`openai/gpt-5-mini`) unless overridden.
  2. When run with `--execute`, each batch is sent to Dedalus/OpenAI (or a mock provider) with instructions defined in `_rubric_instructions`.
  3. Responses are parsed into `CommentAnalysis` records; retries and logging use `DedalusBatchLogContext`.
  4. `_queue_promotion_candidates` inspects analyses for `request_tags` or `PROMOTION_KEYWORDS` hits and enqueues promotion candidates (see next section).
- **Persistence layers:**
  - `comment_llm_store.save_comment_analyses` writes line-delimited JSON to `storage/comment_llm_runs/comment_analyses.jsonl` plus `comment_index.json` for dedup/resume behavior (see `recorded_comment_ids`).
  - `comment_llm_insights_db` (SQLite at `data/comment_llm_insights.db`) stores normalized runs (`comment_llm_runs`) and the latest analysis per comment (`comment_llm_analyses`). Inserts go through `comment_llm_insights_db.insert_run` / `insert_analyses`.
  - Batch metadata can also be exported as structured JSON via `--output-dir`.
- **Consumers:**
  - `comment_llm_insights_service` exposes the stored data to the app (`get_analysis_by_comment_id`, `list_analyses_for_request`, etc.).
  - Request detail pages aggregate tag/urgency/sentiment summaries through `_build_request_comment_insights_summary` and per-comment badges via `_build_comment_insights_lookup`.
  - `/comments/{id}` renders a single comment’s insight card when the analysis exists.
  - Admin dashboard `/admin/comment-insights` + `/api/admin/comment-insights/...` stream recent runs and analyses (templates + JS run in `templates/admin/comment_insights.html` and `static/js/comment-insights*.js`).
  - `wb profile-glaze` (described later) kicks off per-user comment analyses before glazing bios.

## Promotion Queue & Worker

- **Detection:** `_analysis_is_request_candidate` (`app/tools/comment_llm_processing.py`) flags analyses that contain `request_tags` or emergency keywords (`PROMOTION_KEYWORDS`). `_queue_promotion_candidates` then calls `comment_attribute_service.queue_promotion_candidate` to upsert a `promotion_queue` attribute on the source comment with `status=pending`, `reason`, `run_id`, metadata snapshot, and attempt counter.
- **Storage:** Promotion queue entries live entirely in `comment_attributes` rows keyed by `promotion_queue`. Use `comment_attribute_service.list_promotion_attributes` to inspect them programmatically.
- **Worker CLI:** `wb promote-comment-batch` (`app/tools/comment_promotion_batch.py`) has three subcommands:
  - `run` – pull pending entries (default 20), promote each into a full HelpRequest via `comment_request_promotion_service.promote_comment_to_request(source="indexer")`, and update the attribute to `status=completed` or `status=failed` (with error and attempt count).
  - `list` – inspect current queue grouped by status.
  - `retry` – reset a failed/completed item back to pending.
- **Resulting requests:** Promoted requests flow through the same creation logic as manual ones (`request_services.create_request`), so they immediately appear in request listings and feeds.

## Profile Glazing (Composite Flow)

- **Command:** `wb profile-glaze` (`app/tools/profile_glaze_cli.py`)
- **What it does:** For each targeted user, run a scoped `wb comment-llm` execution (with user filters and optional spend caps) and then call the Signal profile snapshot/glazing pipeline to regenerate bios. This is essentially a turnkey “analyze comments + update profile” workflow that reuses the LLM indexing infrastructure described above.

## At-a-Glance Reference

| Pipeline | Entry Points | Key Modules | Storage / Outputs | Primary Consumers |
| --- | --- | --- | --- | --- |
| Chat search index | `wb chat index`, `request_chat_search_service.refresh_chat_index` | `app/services/request_chat_search_service.py`, `app/tools/request_chat_index.py` | `storage/cache/request_chats/request_<id>.json` | Request detail chat search, `/requests/{id}/chat-search`, embeddings, suggestions |
| Chat embeddings | `wb chat embed` | `app/services/request_chat_embeddings.py`, `app/tools/request_chat_embeddings.py` | `storage/cache/request_chat_embeddings/request_<id>.json` | Related-request suggestions, future semantic matchers |
| Related-request suggestions | `request_chat_suggestions.suggest_related_requests` | `app/services/request_chat_suggestions.py` | In-memory payloads derived from caches | Request detail “Related chat mentions” |
| Comment LLM insights | `wb comment-llm` | `app/tools/comment_llm_processing.py`, `app/services/comment_llm_store.py`, `app/services/comment_llm_insights_db.py` | `storage/comment_llm_runs/*`, `data/comment_llm_insights.db` | Request/comment detail pages, admin insights dashboard, profile glazing |
| Promotion queue | `_queue_promotion_candidates`, `wb promote-comment-batch` | `app/services/comment_attribute_service.py`, `app/tools/comment_promotion_batch.py`, `app/services/comment_request_promotion_service.py` | `comment_attributes` records with `key='promotion_queue'` | Auto-creation of HelpRequests from request-like comments |
| Profile glazing | `wb profile-glaze` | `app/tools/profile_glaze_cli.py`, `app/tools/signal_profile_snapshot_cli.py` | Glaze exports under `storage/signal_profiles` (see CLI), relies on insights artifacts | Signal profile bios + downstream analytics |

### Common Operational Recipes

- Rebuild every chat index with heuristic topics only: `wb chat index --all`
- Rebuild chat indexes with LLM tags for the newest 5 comments on each request: `wb chat index --all --llm --llm-latest 5`
- Refresh embeddings for a single request: `wb chat embed --request-id 123 --max-comments 50 --force`
- Run the comment insight pipeline for a tag sweep and execute immediately: `wb comment-llm --snapshot-label housing-drive --help-request-id 77 --batch-size 8 --execute --provider dedalus --max-spend-usd 10`
- Process promotion queue entries that came from the last insight run: `wb promote-comment-batch run --limit 10`
- Fully glaze a member’s Signal profile with fresh comment insights: `wb profile-glaze --username river --comment-skip-existing --comment-max-spend-usd 2`

Use this reference whenever you’re unsure which cache to delete, which CLI to run, or which module is responsible for a given behavior related to comment/request processing.
