# Half-Auth Shadow Publish – Feature Description

- **Problem**: Half-authenticated users can currently draft client-side only. We need their activity (requests, completions, other interactions) to be persisted on the server and promoted automatically once approval completes, without exposing it beforehand.
- **User stories**:
  - As a half-auth user, I want to create and manage requests so that when I’m approved my work appears instantly to the community.
  - As a moderator/admin, I want pending user actions to stay invisible to the public feed until approval so I can vet new users.
  - As a developer, I want a clear staging workflow so pending actions can be promoted safely and audited.
- **Core requirements**:
  - Persist pending requests (and future interactions) in a server-side staging area tied to the user/session.
  - When approval occurs, promote staged items into the live tables atomically; discard or archive on rejection.
  - Update UI: pending dashboard should reflect staged items (e.g., “Your request will publish when approved”).
  - Ensure spec (`docs/spec.md`) and docs describe shadow publish lifecycle.
- **User flow**:
  1. Half-auth user submits a request; system stores it in staging and shows it in their pending view only.
  2. On approval, all staged records are promoted to the live feed and visible to others.
  3. If access is denied, staged records remain private (or are discarded per policy).
- **Success criteria**:
  - Pending activity persists server-side and survives browser/device changes.
  - Promotion on approval publishes staged items without additional user action.
  - Pending UI reflects staged content; full-auth users see the combined feed.
  - Documentation/spec updated with the shadow publish lifecycle.
