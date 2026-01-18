# Intent Capture Guide

This document defines how to capture WhiteBalloon as a set of intentions so the
project can be regenerated from scratch. The intent record is the source of
truth; code is a downstream artifact.

## Principles
- Capture reasons, not diffs. The unit of change is the requirement or decision.
- Treat specifications and plans as executable inputs, not prose.
- Store intent as a dependency graph so causality is explicit.
- Version intent, not just files. Regeneration should be explainable by intent.

## Scope of Intent
Capture intent for product behavior, architecture, constraints, and generation.
At minimum, intent must be sufficient to recreate:
- Core product behaviors (auth, requests, messaging, sync).
- Data models and invariants.
- UI/UX patterns and accessibility expectations.
- CLI and operator workflows.
- Constraints (stack choices, privacy rules, performance limits).
- The generator configuration used to produce code.
- Evaluation artifacts (tests, manual QA checklists, budgets).

## Intent Graph Structure
Represent intent as a content-addressed graph. Each node is a stable record
with explicit dependencies. Recommended node types:
- requirement
- constraint
- decision
- plan
- generator
- environment
- evaluation

Each node must include:
- id: stable slug (kebab-case)
- type: one of the node types above
- statement: canonical, declarative text
- rationale: short explanation of why it exists
- depends_on: list of node ids
- sources: file paths and anchors that informed the node
- acceptance: tests, manual QA steps, or checklists that validate the node

## Canonicalization Rules
- Use stable, declarative statements with "must" or "should".
- Avoid timestamps and author names unless required for traceability.
- Normalize ordering and fields so hashes are stable.
- Keep language concrete and testable; avoid vague adjectives.

## Storage Layout
Create a dedicated intent folder:
- `docs/intent/`
  - `nodes/` (one file per node, YAML or JSON)
  - `graph.json` (root list of node ids and dependency edges)
  - `hashes.json` (node hashes and root hash)

## Capture Workflow
1. Inventory intent sources:
   - `docs/spec.md`, `README.md`, `AI_PROJECT_GUIDE.md`
   - `docs/specs/whiteballoon_modular.md`
   - `docs/plans/` (decisions, tradeoffs, verification)
   - UI/UX references under `docs/design/`, `static/css/`, `templates/`
2. Extract requirements and constraints into nodes.
3. Convert feature plans into decision and plan nodes, including rejected
   alternatives and tradeoffs.
4. Record generator nodes:
   - model family, prompt, templates, tooling, and parameters
   - any fixed seeds or non-determinism controls
5. Record evaluation nodes:
   - tests, scripts, manual QA steps, performance budgets
6. Build the dependency graph so each plan/decision references the
   requirements and constraints that caused it.
7. Compute hashes for each node and the root graph hash.

## Minimum Node Inventory (Starter Set)
Start with these intent areas so regeneration is possible:
- Auth and session lifecycle requirements
- Invite-only registration and admin bootstrap constraints
- Request feed behavior and visibility rules
- Commenting and completion workflow
- Messaging toggle and separate database constraint
- Sync bundle format, signing, and peer workflows
- SSR-first frontend with progressive enhancement
- CLI commands and operator workflows
- Data model invariants (User, Session, HelpRequest, Invite, Comment)
- Design system rules (typography, layout primitives, animations)

## Update Rules
- When behavior changes, update or add intent nodes before code changes.
- When a plan changes, record the new decision and link it to impacted nodes.
- After implementation, verify evaluation artifacts and update acceptance links.
- Keep `docs/spec.md` aligned with intent nodes; it should summarize the graph.

## Example Node Template (YAML)
```yaml
id: req-auth-invite-only
type: requirement
statement: Registration must be invite-only after the first user.
rationale: Protects trust graph and enforces social verification.
depends_on: []
sources:
  - docs/spec.md#L13
  - README.md#L69
acceptance:
  - docs/spec.md#L12
  - tests/services/test_auth_service.py
```

## Regeneration Checklist
Use the intent graph to regenerate:
1. Gather root nodes for the module or capability.
2. Expand dependencies to collect full intent set.
3. Feed requirements, constraints, decisions, and generator nodes to the tool.
4. Generate code, then run evaluation artifacts linked in acceptance fields.
5. Confirm the root hash matches the intent graph version.
