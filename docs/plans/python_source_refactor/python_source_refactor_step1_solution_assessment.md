# Step 1 – Solution Assessment: Python Source Refactor

## Problem Statement
Our largest Python modules (e.g., `app/routes/ui/__init__.py` at 3,182 LOC) slow iteration and obscure ownership; we need smaller files without breaking routing or tooling contracts.

## Option A – Incremental route/package extraction
- **Pros**
  - Minimal disruption: move logical route groups (auth, requests, admin) into dedicated modules while keeping existing FastAPI registrations.
  - Enables gradual testing; each extraction can march behind feature flags or existing integration tests.
  - Fits current review capacity: small PRs scoped to one area don’t block parallel work.
- **Cons**
  - Requires careful dependency untangling; shared helpers may still live in the giant file until later.
  - Multiple partial refactors might leave mixed patterns for a while, increasing mental overhead mid-flight.

## Option B – Full routing re-architecture sprint
- **Pros**
  - Clean slate to redesign package layout, dependency injection, and module boundaries holistically.
  - Opportunity to codify conventions (e.g., per-surface router factories, typed DTO modules) in one pass.
- **Cons**
  - High risk: broad change touches every endpoint, straining QA and increasing merge conflicts.
  - Requires feature freeze or long-lived branch; slows unrelated work and complicates release cadence.

## Option C – Framework-assisted decomposition (codegen/CLI)
- **Pros**
  - Build a tool (e.g., `wb refactor split-routes`) that scaffolds new files, relocates imports, and ensures consistent naming in one command.
  - Reusable automation lowers future refactor costs and enforces standards.
- **Cons**
  - Upfront investment in tooling before any user-visible gains; must maintain the tool itself.
  - Still needs humans to validate nuanced cases (conditional routes, dynamic imports), so may not cover every file.

## Recommendation
Pursue **Option A** first: extract cohesive route groups and helper clusters iteratively. It delivers quick wins, keeps risk manageable, and leaves room to adopt targeted automation (Option C) once patterns stabilize. Save Option B for a future milestone if additional architectural changes are warranted.
