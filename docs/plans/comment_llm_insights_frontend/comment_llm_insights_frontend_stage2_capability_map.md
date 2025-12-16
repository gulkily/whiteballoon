# Stage 2 – Capability Map: Comment LLM Insights Frontend

## Capability 1 – Admin Insights Dashboard
- **Scope**: `/admin/comment-insights` page listing recent runs with status (completed/total batches, provider, model, started_at) and basic filters (snapshot label).
- **Dependencies**: Stage 1 API endpoints (`/api/admin/comment-insights/runs`, `/runs/{id}/analyses`).
- **Acceptance**: Page loads in <2s with at least 10 runs; clicking a run reveals its analyses table without full reload.

## Capability 2 – Run Detail & Comment Drilldown
- **Scope**: Per-run table with inline search/filter; modal/detail view showing the original comment link plus LLM summary/tags.
- **Dependencies**: Capability 1 UI shell; existing admin routes for request/comment links.
- **Acceptance**: Selecting a comment anchors (opens request detail in new tab) and the modal shows structured tags + summary.

## Capability 3 – Inline Preview Hook (request detail)
- **Scope**: For admin users viewing a request, add a badge/icon next to comments that have LLM analyses, linking back to the admin dashboard or showing tooltip summary.
- **Dependencies**: API endpoint to fetch individual comment analysis; capability 2 (so admins can click through for more detail).
- **Acceptance**: Comment rows with analyses show indicator; clicking it either opens modal (if lightweight) or navigates to admin dashboard pre-filtered.

## Capability 4 – CSV Export (runs)
- **Scope**: Allow admins to download a run’s analyses as CSV for external slicing.
- **Dependencies**: Capability 2 (run detail data already available); optional new API endpoint returning CSV.
- **Acceptance**: Export button triggers download within 5s; file includes headers + all analyses currently shown.

## Capability 5 – Feature flag + filtering for user-facing labels
- **Scope**: Introduce a feature flag to control when comment tags/labels are surfaced to general users, and build filtering hooks (e.g., query params or UI inputs) so admins/users can filter comments or runs by tag/type once the flag is on.
- **Dependencies**: Capabilities 2 & 3 (data surfaces) and Capability 4 (export lists). Filtering logic can begin in the admin dashboard and extend to user-facing components when the flag is enabled.
- **Acceptance**: Feature flag off → only admins see tags; flag on → UI shows tags + filter controls (even if still admin-only initially) and can be wired to user-facing contexts later without new plumbing.

## Dependency Overview
1. Capability 1 (dashboard shell)
2. Capability 2 (run detail & drilldown)
3. Capability 3 (inline indicators, optional feature flag)
4. Capability 4 (CSV export builds atop run detail)
5. Capability 5 (permission/flag scaffolding spans others)
