# Social Connections Branch Postmortem

## Context
- Feature: add friend/follow relationships so WhiteBalloon members can intentionally build lightweight social graphs.
- Initial planning (Steps 1–3) was completed and approved before implementation.
- Implementation began on branch `feature/social-connections` but remained unfinished after ~14 hours and was ultimately shelved.

## What Went Wrong
1. **No early integration checkpoint**
   - I focused on the Stage 1 data model/service for too long without verifying it inside the actual app.
   - By the time I wired follow/unfollow routes (Stage 2), the changes were already large and brittle, making iteration slow.

2. **Ad-hoc testing path broke the workflow**
   - The follow/unfollow smoke test tried to delete fixtures with raw SQL strings, which raises `sqlalchemy.exc.ArgumentError` unless wrapped in `text()`. The exception halted the run, and I didn’t immediately back out the helper.
   - Because the test failed before exercising the HTTP routes, I wrongly assumed the server logic might be broken, which sent me back into the code instead of just fixing the helper.

3. **HTMX/fragment handling introduced avoidable complexity**
   - The initial scope only needed JSON responses, but I prematurely added fragment/redirect logic. That extra surface area ate time while offering no confirmed user value yet.

4. **No incremental commits after Stage 1**
   - All Stage 2 work lived in the working tree with no checkpoints. Once the branch felt “stuck,” there was no clean slice to keep vs. drop.

## Why It Happened
- **Insufficient guardrails during implementation**: I didn’t define short checkpoints (e.g., “verify Stage 2 routes via curl” before touching UI contexts).
- **Skipping FastAPI dependency conventions**: I tried to pass `Annotated` parameters out of order, hit `SyntaxError: non-default argument follows default argument`, and lost time rearranging signatures.
- **Testing habits**: I leaned on inline scripts instead of the project’s existing helpers (fixtures, services), so basic cleanup failed.

## How To Avoid This Next Time
1. **Stage-by-stage commits with smoke tests**
   - After each stage, run the smallest possible verification (curl/testclient) and commit immediately—no UI work before Stage 2 endpoints are demonstrably callable.

2. **Use ORM deletes or SQLAlchemy `text()`**
   - When cleaning fixtures, stick to `session.query(Model).delete()` or `session.exec(text("DELETE …"))` so cleanup never blows up before tests run.

3. **Defer HTMX concerns**
   - Build simple JSON/redirect responses first; add HTMX fragments only after the core action is proven and there’s a concrete requirement.

4. **Leverage existing helpers**
   - Reuse the project’s CSRF utilities, visibility guards, and pagination components instead of reimplementing them piecemeal.

5. **Short feedback loops**
   - Define an explicit checklist per stage: data model migrated, endpoint responds 200, UI calls it manually, etc. Don’t move to the next stage until the checklist is green.

## Immediate Actions Before Restarting
- Keep the new Step 1–3 planning docs (already merged) as-is.
- When recreating the branch, start with a target milestone (e.g., “Stage 2 endpoints return JSON”) and capture each success in the Step 4 summary to enforce cadence.
