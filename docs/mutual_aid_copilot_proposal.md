# WhiteBalloon Residency Proposal – Mutual Aid Copilot

## 1. Background & Motivation
WhiteBalloon is a distributed mutual-aid network designed for hacker houses, residencies, and adjacent communities. Each node controls its own data custody and only propagates information users explicitly mark as shareable. Identity can be fragmented—first name public, last name/email limited to a local instance—so trust decisions stay human-centric. Dedalus Labs’ managed MCP gateway offers the connective tissue we need to plug multiple LLMs into our FastAPI routes and CLI tools, with autoscaling, telemetry, and reliability built in.

## 2. Project Summary
We propose the “Mutual Aid Copilot”: a Dedalus-backed agent that lives inside the WhiteBalloon admin UI. Admins can triage new requests, suggest privacy changes for requests or comments, recommend community members to connect with, and prep sync bundles for peer instances—all via natural language. Dedalus exposes these workflows as MCP tools so the copilot can orchestrate local scripts and remote services transparently.

## 3. Residency Plan (3 Weeks)
### Week 1 – Tool Modeling & Integration
- Map the highest-impact admin actions (request audit, scope toggle, invite generator, sync exporter, connector suggestions).
- Implement each action as a Dedalus MCP tool, tying into our existing FastAPI endpoints and CLI commands.
- Embed the initial Mutual Aid Copilot experience inside the WhiteBalloon admin dashboard.

### Week 2 – User Testing & Documentation
- Run scenario tests with WhiteBalloon admins across multiple hubs; measure accuracy and time saved.
- Iterate on guardrails, prompts, and tool metadata based on feedback.
- Write deployment instructions so any WhiteBalloon instance can provision the copilot with Dedalus credentials.

### Week 3 – Hardening & Enhancements
- Address issues surfaced during testing (permissions, latency, multi-tool chains).
- Add requested improvements (batch operations, richer explanations, better connector suggestions).
- Capture success metrics: requests triaged per hour, privacy-error rate, hours saved.

## 4. Deliverables
- Production-ready Mutual Aid Copilot hosted via Dedalus MCP gateway.
- Open-source MCP tool definitions for core WhiteBalloon admin workflows.
- Admin UI module + docs so any instance can enable the copilot quickly.
- Launch collateral: metrics plus (optional) joint blog or webinar featuring Dedalus.

## 5. Support Requested
- Residency mentorship and API credits to test multiple LLM backends (general reasoning + policy/fact checkers).
- Access to Dedalus autoscaling, rate limiting, and telemetry features.
- Opportunities to showcase the outcome (case study, blog, webinar).

## 6. Extra Highlights to Brag About
- **Federated-first architecture:** Each WhiteBalloon node keeps its own database, signing keys, and sync policies, proving that privacy-preserving federation is possible.
- **Fine-grained identity controls:** Users can expose only the exact fields they want, making the network friendly for privacy-conscious communities.
- **Mutual-aid specific UX:** Purpose-built flows (request triage, invite graphs, sync bundles) mean Dedalus is enabling a real civic-tech use case.
- **Operational tooling already in place:** WhiteBalloon ships with `.sync` bundles, CLI automation, and open-source skins—Dedalus plugs into a mature foundation.
- **Launch momentum:** We plan to go live mid-December, so the residency aligns with a high-visibility rollout.
- **Open-source impact:** Everything built in the residency becomes reusable for other mutual-aid and DAO-style projects.
- **Security posture:** Signed bundles, per-instance data custody, and auditable privacy toggles ensure Dedalus is showcased in a security-conscious environment.

This collaboration would demonstrate how Dedalus powers a sensitive, real-world agent that blends local tools, remote services, and multiple LLMs—all while helping communities coordinate care.
