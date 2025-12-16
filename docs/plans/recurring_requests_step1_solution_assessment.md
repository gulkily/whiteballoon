# Recurring Requests · Step 1 Solution Assessment

**Problem statement**: House managers need a lightweight way to recreate recurring needs (chores, meetings) either as author-only drafts awaiting approval or as auto-published help requests without rewriting the same details every cycle.

**Option A – In-app scheduler that clones draft templates**
- Run an internal background loop (bootstrapped with the web server) that duplicates pre-approved template requests into `draft` entries assigned to the house manager for review; no external cron required.
- Pros: Keeps publishing manual (no accidental spam), reuses new draft infrastructure, simple rollback (delete the draft). Works without touching request feed logic.
- Cons: Still requires manual publish each cycle; delays if manager forgets; needs persistence for templates + scheduler config.

**Option B – Auto-publish recurring templates**
- Allow templates to specify cadence + publish mode; scheduler posts full help requests on schedule (skipping drafts entirely).
- Pros: Zero-touch recurring posts, ensures community sees requests on time, useful for reminders (meetings, dues) where approval isn’t needed.
- Cons: Higher risk of noise/typos going live, must ensure unique IDs + pins don’t explode; requires notification/undo path.

**Option C – Client-side “duplicate last request” action**
- Add UI button to copy an earlier request into the form (optionally saving as draft) with no server automation.
- Pros: Minimal backend work, immediate reuse from existing history, no scheduler needed.
- Cons: Still manual for each recurrence, doesn’t ensure cadence, only works when manager remembers to click.

**Recommendation**: Option A combined with opt-in auto-publish toggle later. Start with scheduled draft clones so house managers retain control, leveraging the new draft APIs; it mitigates accidental spam and keeps implementation small. We can extend templates with “publish automatically” if the workflow proves safe.
