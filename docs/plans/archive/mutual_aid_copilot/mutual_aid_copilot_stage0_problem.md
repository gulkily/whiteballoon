# Mutual Aid Copilot – Stage 0 Problem Statement

**Problem.** Volunteer admins across hacker houses and residencies handle every incoming WhiteBalloon request manually: triaging, adjusting privacy scopes, recommending connectors, and queuing sync bundles. Those workflows are repetitive, time-consuming, and error-prone when multiple instances are federating data. Without an automation layer, we risk burning out admins, delaying help for members, and blocking the mid-December launch with Dedalus Labs.

**Pain points.**
- No unified way to run LLM-powered suggestions against WhiteBalloon’s FastAPI/CLI tooling; every task requires context switching.
- Privacy toggles on requests/comments are entirely manual, producing inconsistent propagation to other instances.
- Sync bundle prep happens ad hoc; admins must remember CLI commands and key management details.
- Hacker house operators constantly ask who can help with resource X—but WhiteBalloon cannot proactively search/match today.

**Success metrics.**
- ≥50% reduction in admin time per triaged request week-over-week.
- Zero privacy-scope mismatches reported during launch month (measured via bundle audits).
- At least three communities running the copilot with their own Dedalus API keys by end of residency.

**Guardrails.**
- Must rely on Dedalus Labs’ managed MCP gateway—no bespoke LLM infra.
- Keep per-instance data custody intact; only explicitly shared data leaves a node.
- Deliver within three-week residency timeline, aligned with mid-December public launch.
