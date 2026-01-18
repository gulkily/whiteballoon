# User Messaging System – Step 1 Solution Assessment

**Problem statement**: Per `AI_PROJECT_GUIDE.md` and `docs/spec.md`, let members exchange direct messages inside the existing modular monolith, give admins a single toggle to enable/disable messaging, and store every message in a separate database for isolation/compliance.

## Option A – Multi-DB module inside existing app
- Pros: Fits the modular pattern (`app/modules/<feature>`) described in the project guide, reuses existing auth/session context for ACLs, lets us introduce a dedicated SQLModel engine (e.g., `data/messages.db`) while keeping FastAPI + `./wb` tooling unchanged, and exposes the admin toggle via the existing settings/scope UI.
- Cons: App servers manage two transactional stores so migrations/backups for the messaging DB must be coordinated carefully, and we must keep cross-DB transactions simple (e.g., avoid chat↔request joins) to preserve reliability.

## Option B – Dedicated messaging microservice
- Pros: Clean separation of scaling concerns, messages live in their own service+database boundary, and admin enablement can be exposed via a REST/gRPC contract for future clients or CLI tools.
- Cons: Highest time-to-value (new repo, deployment, alerting, auth proxy) that duplicates much of the functionality cataloged in `README.md`/`docs/spec.md`, introduces new secrets/routing to keep sessions in sync, and adds infra cost for what is currently a single FastAPI app.

## Option C – Event queue + worker writing to messaging DB
- Pros: Frontend/API stays responsive because writes are queued, retryable job pipeline offers resilience, and workers can evolve (analytics, retention policies) without touching the request path or the synchronous FastAPI request lifecycle.
- Cons: Adds queue infrastructure plus worker orchestration, admin “enable messaging” changes may still need synchronous coordination, and user-facing consistency suffers if the queue lags.

**Recommendation**: Option A — extending the current app with a scoped multi-database messaging module keeps delivery fast, surfaces admin toggles in the same UI/CLI pathways the docs already endorse, and still satisfies the separate-database mandate without the operational overhead of new services or queues.
