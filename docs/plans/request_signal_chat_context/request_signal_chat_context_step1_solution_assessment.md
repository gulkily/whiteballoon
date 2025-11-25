## Problem
Signal chats imported as linear comments under a single request become buried context, making it difficult to resurface relevant promises, contacts, or decisions when working on future requests.

## Options
- **Option A – Leave chat as-is and rely on manual search/links**
  - Pros: Zero new tooling, we can encourage humans to cross-link or quote comments into new requests on demand.
  - Cons: High cognitive load, hard to remember what exists, no structured metadata to enable proactive surfacing.
- **Option B – Introduce manual "insight" objects tied to comment ranges**
  - Pros: Lightweight CRUD to capture distilled facts (e.g., "Alice can help with housing"), tag them with people/topics, and link both the original conversation and any relevant requests; enables feeds and reminders without automation risk.
  - Cons: Requires discipline to summarize chats, introduces another UI surface, and still depends on humans to notice when insights should be created.
- **Option C – Automate extraction via semantic tagging/embeddings**
  - Pros: Run embeddings or keyword heuristics on the imported chat to automatically surface related insights when a new request shares entities/topics; scales once pipelines exist.
  - Cons: Considerable engineering (background jobs, vector store, tuning), noisy matches without high-quality training data, and harder to explain to users.
- **Option D – Capture follow-up tasks or request links directly from chat**
  - Pros: Create lightweight cross-links so specific chat messages can spawn tasks or reference other requests, keeping the original context but making it discoverable via backlinks or per-person timelines.
  - Cons: Still leaves the information in long-form text, requires UI affordances for quoting/linking, and can become noisy if every message spawns a task.
- **Option E – Add targeted search across chat comments**
  - Pros: Index the imported chat so responders can search by person, keyword, or tag without leaving the request, making it faster to answer “who promised X?” or “when was housing mentioned?”
  - Cons: Only helps when someone remembers to search, provides no structured metadata for proactive surfacing, and requires search infra (indexing, permissions) that we’d otherwise avoid.

## Recommendation
Pursue Option E (targeted search) immediately to make the imported chat usable with minimal lift, then layer in Option C’s automated surfacing once the search index and tagging vocabulary exist. This sequence gives responders quick wins now while preparing the data pipelines needed for meaningful automation later.
