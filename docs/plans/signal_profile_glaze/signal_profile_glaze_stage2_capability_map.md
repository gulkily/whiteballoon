# Signal Profile Glaze – Stage 2 Capability Map

We are committing to a profile experience that glorifies every Signal-imported participant: bios must sound celebratory, elevate their contributions, and surface flattering receipts (links, stats) without inventing facts. The chosen architecture piggybacks on the existing Signal importer + comment LLM pipeline, adds an aggregation layer that distills per-user highlights, stores those bios as refreshable attributes, and renders them in the member profile UI with provenance + shareable links.

## Capability Inventory

### 1. Signal Identity Snapshotter
- **Scope**: Gather all artifacts about a Signal participant across WB data stores (User rows, `UserAttribute` Signal metadata, seeded request comments, attachment/link references). Emit a normalized per-user snapshot (counts, first/last activity, distinct URLs/domains, reaction emojis) that downstream jobs consume. Runs as an idempotent CLI command or scheduled task.
- **Dependencies**: Requires the Signal importer outputs (`signal_member_key:*`, seed help request IDs) and read access to request comments / attachments.
- **Acceptance Tests**:
  - Given an imported chat, generating a snapshot for a mapped user produces correct counts and timestamps (matches DB queries).
  - Users without Signal data yield a noop snapshot.
  - Snapshotter is rerunnable; running twice without new data produces identical payloads.

### 2. Positivity-Tuned Bio Generator
- **Scope**: Feed each snapshot plus existing LLM comment analyses into a deterministic prompt template that enforces “talk them up” tone rules (celebratory adjectives, highlight resources they shared, avoid negatives unless substantiated). Produces: (a) 2–3 sentence glossy bio, (b) list of flattering proof points (top tags, notable links), (c) quote-ready pull lines. Includes guardrails (max length, forbidden phrases) and logging of raw prompts/responses for audits.
- **Dependencies**: Needs snapshots (Capability 1) and comment analysis records from `comment_llm_insights_db`. Requires secrets/config for the selected LLM provider.
- **Acceptance Tests**:
  - Prompt renders deterministic scaffolding given fixture data; snapshots with missing fields still yield positive copy (falls back to personality adjectives derived from tags/reactions).
  - Responses never contain disallowed tones/phrases (automated regex check) and always cite at least one concrete reference (link/tag/timeframe) from the snapshot when available.
  - When analyses/tags are neutral or negative, the generator reframes them positively (e.g., “has navigated complex housing logistics”) while staying truthful.

### 3. Profile Insight Store & Freshness Manager
- **Scope**: Persist generated bios + proof points as structured rows (`user_profile_highlights` table or dedicated JSON attribute). Track provenance (source chat slug, last LLM run, inputs hash) and expose an API/service for reads. Add staleness detection: mark bios stale after configurable days or if new Signal messages arrive, and enqueue regeneration. Includes operator tooling to inspect runs and override bios if needed.
- **Dependencies**: Consumes outputs from Capability 2; integrates with DB migrations, background job scheduler, and admin UI logging.
- **Acceptance Tests**:
  - Writing a highlight overwrites prior entry atomically and stores provenance metadata.
  - Staleness detector marks entries stale when new comments exist beyond the stored `last_message_at`.
  - Manual override path keeps operator text locked while still recording new data arrivals for later review.

### 4. Glazed Profile Presentation
- **Scope**: Update `/profile` (member view) and `/admin/profiles` (ops view) to render the bio block, proof points, and “receipts” links (Signal seed request, extracted external URLs). Include friendly microcopy (“Community perception”) and CTA chips for request/comment history. Respect permissions (only members/admins see Signal-derived details). Add analytics instrumentation to measure views/interactions.
- **Dependencies**: Requires Capability 3 API, existing profile routes/templates, and knowledge of which users have Signal data. UI depends on design tokens/static assets.
- **Acceptance Tests**:
  - Profile pages show the glazed bio when available, fall back gracefully otherwise.
  - Each proof point links back to verifiable data (request/comments/URL) and opens in new tab when external.
  - Admin view exposes provenance + “regenerate now” control hooked into Capability 2/3.

## Dependency Graph

| Capability | Depends On | Notes |
|------------|------------|-------|
| Signal Identity Snapshotter | — | Foundation layer; can ship alongside instrumentation.
| Positivity-Tuned Bio Generator | Snapshotter | Needs normalized inputs + tag data.
| Profile Insight Store & Freshness Manager | Bio Generator | Stores the generated payloads + staleness tracking.
| Glazed Profile Presentation | Insight Store | Renders stored bios/proof points and triggers refreshes.

```
Snapshotter → Bio Generator → Insight Store → Glazed Profile UI
```

## Open Questions / Risks
- How do we handle users who appear in multiple Signal groups with conflicting tones? (May need multi-source attribution in Capabilities 1–3.)
- Should bios be regenerated automatically when LLM prompt template changes, or do we migrate stored text? (Impacts Capability 3’s staleness hashing.)
- How far can we lean into “glazing” without misrepresentation? Need policy review + maybe human approval queue.
