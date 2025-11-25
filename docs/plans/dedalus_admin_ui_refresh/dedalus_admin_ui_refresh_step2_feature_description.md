# Dedalus Admin UI Refresh – Step 2 Feature Description

## Problem
The `/admin/dedalus` page presents every status, action, and form inside one tall card, so admins must scan dense paragraphs to know whether the API key exists, when it was last verified, or if a manual check is running. The lack of visual hierarchy slows audits and invites mistakes when toggling keys versus verifying connectivity.

## User Stories
- As an admin, I want the page to tell me immediately whether Dedalus is connected (key stored, last verification, outstanding job) so I know if I can trust the Mutual Aid Copilot.
- As an admin, I want verify/log actions grouped with the status panel so I can trigger a re-check or pivot to the activity log without scrolling past the API key form.
- As a security steward, I want the API key management area to clearly explain whether a key is stored, whether I’m replacing or removing it, and what will happen on save.
- As a support engineer, I want queued jobs and recent results surfaced with badges so I can confirm background work before escalating an incident.

## Core Requirements
- Split the page into two primary panels: **Verification status & actions** and **API key management**, each with a titled header, tinted background, and clear borders; stack vertically on narrow screens but present side-by-side (two-column) on desktop widths.
- In the verification panel show a summary block with badges for “Key stored?”, “Last verified <relative time>”, and “Latest job status” using success/warning/error colors pulled from existing UI tokens.
- Keep the `realtime_status` component but restyle the container to resemble a timeline card beneath the summary, with room for tooltip text or small captions that explain what each row means.
- Group interactive controls (Verify button, “View activity log” link) in a button row anchored within the verification panel so they are visually associated with the statuses.
- Move the alert that displays the latest verification message into the verification panel with contextual iconography so success or failure is obvious without reading paragraphs.
- Ensure the API key panel keeps the existing form fields but adds a short “Key storage” summary at the top, clarifies the behavior of the “Remove stored key” checkbox, and uses consistent spacing/labels so the form feels lighter.
- Confirm the layout remains accessible: headers use semantic tags, buttons keep aria labels/tooltips where necessary, and tab order flows left-to-right then top-to-bottom.

## User Flow
1. Admin opens `/admin/dedalus` and immediately sees two panels; the left/top verification panel lists key/verification state badges and any current job updates.
2. If verification looks stale, admin clicks “Verify connection” within the same panel; the button triggers the existing job and the status timeline updates inline.
3. For deeper investigation, admin taps “Open activity log,” landing on `/admin/dedalus/logs` in a new tab or same tab per browser defaults.
4. If the API key must change, admin uses the right/bottom panel to paste a new key or check “Remove stored key,” reviews the summary text, and clicks “Save API key.”
5. After saving, the verification panel surfaces the automatic post-save verification result so the admin confirms the new key works.

## Success Criteria
- An admin can determine whether a Dedalus key is stored and when it was last verified within 3 seconds of page load (verified via usability QA).
- Verification-related actions (verify, logs) are contained in the same visual panel as status indicators on all breakpoints ≥1024px, reducing the need to scroll for 90th-percentile users.
- Alerts and badges use existing success/warning/error tokens, passing WCAG AA contrast checks.
- Mobile layout stacks the panels with no controls clipped or hidden (tested on 375px viewport).
- No backend behavior changes are required; all existing forms and job triggers continue working after the UI refresh.
