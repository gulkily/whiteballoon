# Caption Personalization · Step 2 Feature Description

**Problem**: Helper captions are essential for onboarding but clutter the UI for long-time members. We need a way to serve both audiences without rewriting every page from scratch.

**User stories**
- As a new member, I want to see contextual captions that explain actions (e.g., “Pinned requests show priority needs”) so I know how to use the UI.
- As an experienced member, I want a quick global setting to hide helper captions so the interface feels clean once I no longer need reminders.
- As a power user, I want to dismiss individual captions (“👍 Got it”) so I can hide just the ones I already understand while keeping others visible.

**Core requirements**
1. Introduce a global “Hide helper captions” toggle in account settings (default off) that suppresses non-critical captions for the user across the product.
2. Add lightweight per-caption dismiss buttons (thumbs-up “Got it” micro-control) that store a dismissal state per user, overriding the global toggle if captions are still enabled.
3. Provide a central registry/enum for caption IDs so components can opt into the personalization system without copy-pasting logic.
4. Expose a helper API/templating function to render captions with the proper controls (shows dismiss button, respects global/off state, etc.), minimizing duplication.
5. Ensure dismissals sync between web sessions (store in DB/user attributes), and provide a way to reset them (global “Show captions again” link near settings).

**Shared component inventory**
- `app/models.py` or user attribute store: persist per-user global toggle + per-caption dismiss flags (likely via JSON field/user attributes table).
- `templates/*` (requests index, menu, etc.): wrap existing captions in the new helper macro so they can be hidden/dismissed consistently.
- `static/js/*` (if needed) for handling the thumbs-up “Got it” action via fetch/post without page reloads.
- `app/routes/ui/settings.py` (or equivalent) to add the “Hide helper captions” toggle and reset action.

**User flow**
1. New member signs in; captions render normally with a tiny 👍 button. Clicking “Got it” stores dismissal and hides the caption immediately.
2. After gaining confidence, the member opens Settings → Account and enables “Hide helper captions,” which suppresses all helper blips unless individually re-enabled.
3. If they want captions back, they toggle the setting off or click “Reset captions,” which clears dismissals and re-renders captions.
4. (Future backlog) Admin visibility into caption state can be revisited later once user-facing personalization ships.

**Success criteria**
- Global toggle hides captions across at least three major surfaces (Requests page, Menu, Invite pages) for a user after enabling it.
- Per-caption thumbs-up dismiss works without a full page reload, persists across sessions, and can be reset.
- Captions still render for new users (toggle off + no dismissals) with the helper UI intact.
- UX remains accessible: thumbs-up button is keyboard operable, and captions have aria labels indicating dismiss action.
