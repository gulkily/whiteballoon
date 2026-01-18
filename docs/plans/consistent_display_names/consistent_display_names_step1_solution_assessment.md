# Consistent Display Names – Step 1: Solution Assessment

**Problem statement**: Profile links on request detail headers/cards still show plain usernames (or “Community member”) while chat/comment areas already use nicer display names; we need a consistent identity presentation everywhere.

## Option A – Reuse existing Signal display-name lookup for requests (recommended)
- **Pros**: Minimal scope by leveraging the maps already loaded for chat/comments; consistent experience across /requests/* pages without touching invite/auth flows; low-risk refactor since the data already exists in memory.
- **Cons**: Still falls back to usernames when no Signal display name is available; requires threading another optional field through templates and API serializers.

## Option B – Introduce a first-class “profile display name” attribute
- **Pros**: Creates a single canonical display name per user that works beyond Signal-imported threads; future features (members directory, CLI output) gain a uniform field.
- **Cons**: Requires migrations/UI to collect the name, copy jobs for legacy Signal data, and broader QA to ensure privacy controls respect the new attribute; longer timeline for a narrow UX issue.

## Recommendation
Pursue **Option A**: extending the existing Signal display-name helper to request metadata delivers the desired consistency quickly while keeping the door open for a more ambitious global display-name system later.
