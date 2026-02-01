# Step 1: Solution Assessment — /llms.txt for running instance

Problem statement: Provide a repository-root `/llms.txt` that clearly explains how agents should engage with a running WhiteBalloon instance and reflects the current configuration.

Option A — Static `/llms.txt` maintained in repo
- Pros: Lowest effort; immediately visible to agents; can directly mirror `.env` and documented routes; no runtime changes.
- Cons: Requires manual updates when configuration changes; risk of drift if operators forget.

Option B — Generated `/llms.txt` from config at runtime
- Pros: Always matches live settings; can surface enabled feature flags and base URL reliably.
- Cons: Requires code changes (new route or build step); adds complexity and deployment considerations; not a simple static file for repo consumers.

Option C — Scripted update (`./wb update-llms`) that rewrites `/llms.txt` from `.env`
- Pros: Keeps file static while reducing drift; minimal app changes.
- Cons: Another CLI path to maintain; still relies on operators to run it.

Recommendation: Option B. It best matches the requirement that the file reflect live configuration and keeps the agent view aligned with the running instance even as settings change.
