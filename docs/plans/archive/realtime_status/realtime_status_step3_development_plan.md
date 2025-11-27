# Step 3: Development Plan – Realtime Status Feedback

1. **Stage 1 – Catalog Async Admin Actions**
   - **Goal**: Enumerate every admin-triggered async process (Push, Pull, Dedalus tests, etc.) and document current endpoints + status handling gaps.
   - **Dependencies**: Access to admin action specs/API list.
   - **Changes**: Create inventory doc/table noting endpoint, trigger, existing job ids (if any), and logging behavior.
   - **Verification**: Review with admin stakeholders; confirm all current actions captured.
   - **Risks**: Missing hidden/cron-triggered flows would leave gaps for later stages.

2. **Stage 2 – Backend Job Contract + Transport**
   - **Goal**: Define shared job status schema and the transport (SSE/WebSocket) API for pushing updates with polling fallback endpoint.
   - **Dependencies**: Stage 1 inventory, existing realtime infrastructure capability.
   - **Changes**: Add backend module for job orchestration (status model/interface, serializer, SSE hub, `/jobs/:id/status` polling endpoint).
   - **Verification**: Unit test serializer + SSE stream; manually hit SSE endpoint ensuring updates follow schema.
   - **Risks**: Server resource usage under many concurrent subscriptions; transport mismatch with hosting limitations.

3. **Stage 3 – Logging & Persistence Layer**
   - **Goal**: Persist job lifecycle data (start/end timestamps, status, summary) for auditing and future API queries.
   - **Dependencies**: Stage 2 schema finalized.
   - **Changes**: Extend existing job/task tables or add lightweight store; ensure write hooks on status changes, add query endpoint for history.
   - **Verification**: Manual run of representative jobs verifying DB rows/log entries; API fetch returns latest entries.
   - **Risks**: Extra DB writes on high-volume jobs; schema mismatch with existing analytics tooling.

4. **Stage 4 – Frontend Status Component**
   - **Goal**: Build reusable UI component (state machine, progress, timestamps, error surface) + styling guidelines.
   - **Dependencies**: Stage 2 schema to know payload fields.
   - **Changes**: Create component, CSS tokens, copy, and documentation snippet demonstrating embed next to action buttons.
   - **Verification**: Storybook/manual render tests covering in-progress/success/failure/warning states.
   - **Risks**: Accessibility regressions (color contrast, screen readers) if not tested.

5. **Stage 5 – Realtime Subscription + Polling Hook**
   - **Goal**: Implement frontend data hook/service handling SSE subscription with automatic polling fallback and retries.
   - **Dependencies**: Stage 2 transport endpoints, Stage 4 component to consume updates.
   - **Changes**: Add hook/service module, configure exponential backoff, shareable context for multiple simultaneous jobs.
   - **Verification**: Manual test via mocked server sending staged updates; confirm fallback triggers when SSE disabled.
   - **Risks**: Memory leaks from dangling subscriptions; hammering server if polling not throttled.

6. **Stage 6 – Integrate Actions + QA**
   - **Goal**: Wire component + hook into each admin action flow (Push, Pull, Dedalus test, others), ensure backend endpoints emit job ids immediately.
   - **Dependencies**: All previous stages complete.
   - **Changes**: Update action handlers to return job metadata, render component in admin UI, ensure logs written per Stage 3.
   - **Verification**: Manual QA run: trigger each action, observe transitions, confirm logs; include smoke test checklist in Step 4 summary.
   - **Risks**: Legacy code paths bypass new status component; inconsistent translation/copy across screens.
