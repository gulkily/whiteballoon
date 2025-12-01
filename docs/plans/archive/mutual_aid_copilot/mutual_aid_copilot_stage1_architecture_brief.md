# Mutual Aid Copilot – Stage 1 Architecture Brief

## Option A – MCP Orchestrator on Dedalus (preferred)
- **Flow:** WhiteBalloon exposes admin actions (audit request, toggle scope, recommend connector, prep sync bundle) as HTTP/CLI tools. Dedalus MCP gateway brokers any LLM to these tools via a single endpoint. Mutual Aid Copilot UI calls Dedalus, which routes to LLM + tools.
- **Trade-offs:** Requires well-defined tool schemas and API stability, but offloads autoscaling, retries, and LLM vendor management to Dedalus. Latency depends on Dedalus round-trip, acceptable for admin workflows.
- **Reuse:** FastAPI routes (`/admin/...`), sync CLI commands in `tools/dev.py`, `.sync` bundle infrastructure.

## Option B – Local Orchestrator + Dedalus as fallback
- **Flow:** Run a local agent service alongside WhiteBalloon. Dedalus is only used when calling external tools; core orchestration is homegrown.
- **Trade-offs:** More control over latency and data localization but duplicates the orchestration layer we’d get “for free,” and reintroduces scaling/ops burden.
- **Reuse:** Same as Option A but adds new service to deploy and monitor.

## Option C – Per-instance scripts with minimal MCP use
- **Flow:** Provide scripts that call LLM APIs directly per admin machine; Dedalus is optional. Minimal integration work.
- **Trade-offs:** Zero infrastructure lift but yields inconsistent behavior, difficult auditing, and no shared telemetry—fails residency goals.

### Decision
Option A selected. It maximizes Dedalus’ managed MCP gateway, aligns with residency value prop, and keeps our ops lean. Unknowns: precise tool schema, auth model for Dedalus API keys, and how to stream context (requests/comments) securely.

### Open Questions
1. How do we store per-instance Dedalus API keys securely (.env, encrypted store)?
2. Do we need multi-LLM routing (general reasoning vs. policy guard) within Dedalus, or can we start with one model?
3. What telemetry hooks are required so Dedalus can expose usage dashboards to instances?
4. Should we feature-flag each MCP tool to allow phased rollout per community?

### Next Steps
- Enumerate the capabilities (tools + UI + credentials) in Stage 2.
- Define data contracts for each action (request payload, scope toggle command, connector suggestions) and how context flows into Dedalus (limited to explicitly shared data).
