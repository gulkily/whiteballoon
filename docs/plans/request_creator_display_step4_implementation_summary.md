## Stage 1 – Expose creator metadata
- `RequestResponse` now includes an optional `created_by_username`, populated via a shared `load_creator_usernames` helper that batches user lookups for each request list.
- Server-rendered views reuse the helper during serialization so half-auth and fully authenticated sessions receive the same enriched payloads.

### Testing
- Manual: Pending — need to hit `/api/requests` and confirm username values appear for recent and older requests.
