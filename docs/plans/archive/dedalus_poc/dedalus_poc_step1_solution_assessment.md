# Dedalus POC Integration – Step 1 Solution Assessment

**Problem:** We need a quick proof-of-concept showing Dedalus Labs can drive WhiteBalloon admin workflows before the residency begins.

## Option A – CLI-based Verification Script (Recommended)
- Hook Dedalus SDK into a simple script that runs one of WhiteBalloon’s existing CLI commands (e.g., request audit) via MCP.
- Pros: Fastest to build, exercise real tools, demonstrates Dedalus runner + MCP integration immediately.
- Cons: No UI exposure yet; manual trigger only.

## Option B – Admin UI Button Triggering Dedalus
- Add a temporary button in `/admin/profiles` that calls Dedalus to summarize a request.
- Pros: Visible in UI, closer to final experience.
- Cons: Requires more wiring (UI + backend), still limited functionality.

## Option C – Standalone Notebook (manual context)
- Run Dedalus runner in a Jupyter notebook with mocked WhiteBalloon data.
- Pros: Minimal code changes, easy to iterate.
- Cons: Doesn’t exercise real APIs or MCP tools; weak signal.

## Recommendation
Go with **Option A** (CLI-based verification script). It touches real WhiteBalloon tooling, keeps scope small, and gives us a concrete artifact to show Dedalus before the residency. Once that POC works, we can expand into the admin UI (Option B) within the Stage 3 plan.
