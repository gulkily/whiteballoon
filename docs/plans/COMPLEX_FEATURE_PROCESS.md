# Complex Feature Process

When pursuing multi-instance sync or other large-scale features, use this five-stage process to force clarity before touching code. Each stage produces a short artifact in `docs/plans/` (≤1 page unless noted) and must be approved before moving on. Keep each stage’s doc uncommitted until reviewed, then commit right before starting the next stage so pending work stays visible. The outcome is a detailed description (or set of descriptions) that feeds directly into the FEATURE_DEVELOPMENT_PROCESS planning docs—development must not begin until both processes conclude.

## Stage 0 – Problem Framing
**When**: At the first hint of cross-cutting impact (infra, data sync, multiple orgs, external integrations).
- Deliverable: `docs/plans/<feature>_stage0_problem.md`
- Content: One-paragraph problem statement, current pain points, top-level success metrics, explicit guardrails (time/tech).
- Goal: Align on why this feature matters and what “done” means before solutioning.

## Stage 1 – Architecture Brief
**Purpose**: Sketch the viable solution spaces and trade-offs.
- Deliverable: `*_stage1_architecture_brief.md`
- Content: 2–3 architectural options (diagram or bullet list), trade-offs (latency, consistency, ops), existing components to reuse, data contracts to touch.
- Format: ≤1.5 pages, include lightweight diagram or structured list.
- Outcome: Pick a direction and enumerate open questions.

## Stage 2 – Capability Decomposition
**Purpose**: Break the chosen architecture into independently shippable capabilities.
- Deliverable: `*_stage2_capability_map.md`
- Content: List of capabilities (e.g., “Instance discovery”, “Sync queue”, “Conflict resolver”), for each: scope, dependencies, acceptance tests.
- Add a dependency graph/table showing sequencing.

## Stage 3 – Implementation Playbook
**Purpose**: Turn capabilities into actionable work packages.
- Deliverable: `*_stage3_playbook.md`
- Content: For each capability: step-by-step tasks (≤1 hr or ≤75 LoC each), data/API changes, rollout/ops plan, verification strategy (unit/integration/load), fallback plan.
- Include instrumentation/logging requirements and feature-flag strategy.

## Stage 4 – Execution Logs
**Purpose**: Track progress and guard against drift.
- Deliverable: `*_stage4_execution_log.md`
- Content: Table per iteration: date, stage/task, code refs, tests run, open risks.
- Update after each merged increment. Serves as living changelog.

## Stage 5 – Post-Implementation Review
**Purpose**: Capture outcomes and follow-ups.
- Deliverable: `*_stage5_postmortem.md`
- Content: What worked, what didn’t, perf metrics vs targets, remaining debt, next bets.
- Include checklist: docs updated, ops handoff done, dashboards/alerts live.

## Rules of Engagement
- No coding before Stage 2 sign-off.
- Keep each doc concise; link to detailed diagrams/spikes elsewhere.
- Highlight “unknowns” in every stage; unresolved unknowns block downstream work.
- For multi-instance sync, explicitly call out consistency model, failure handling, and migration/rollback plan.
- Store diagrams (mermaid/png) under `docs/plans/diagrams/` and reference them in the relevant stage file.
- Reuse the process for any feature touching more than one subsystem or requiring staged rollouts.
