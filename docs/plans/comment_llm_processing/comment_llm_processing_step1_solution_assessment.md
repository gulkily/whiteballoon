# Step 1 – Solution Assessment: Comment LLM Processing

**Problem**: We need a reliable way to run all existing help-request comments (≈7.3k, ~221k tokens) through an LLM to surface insights without blowing through budget or pipeline capacity.

**Option A – Single-comment worker (baseline)**
- **Pros**: Simplest to implement; minimal prompt engineering; easy retry/accounting per comment; no risk of context overflow.
- **Cons**: 7k+ individual API calls → higher latency/overhead; harder to keep OpenAI rate limits satisfied; cost per token slightly higher due to repeated instructions.

**Option B – Batched prompts (~10 comments per request)**
- **Pros**: Cuts API overhead by ~10x; easier to stay within provider rate limits; cheaper because shared instructions amortized per batch; natural place to summarize related comments together.
- **Cons**: Requires chunking logic, deterministic pagination, and per-comment attribution inside a shared response; more complicated error handling when one batch fails.

**Option C – Embed comments, process offline**
- **Pros**: One-time embedding pass + offline analysis avoids expensive generative tokens; can reuse vectors for future features.
- **Cons**: Doesn’t satisfy “run through language model” requirement for narrative outputs; still ~7k embedding calls; adds custom analysis stack.

**Recommendation**: Option B. Batching comments (5‑15 per call depending on prompt size) balances simplicity with throughput, keeps requests well under 128k-token limits, and cuts cost by reducing repeated system/user instructions. We can fall back to Option A for comments that fail batching, so the risk is manageable.
