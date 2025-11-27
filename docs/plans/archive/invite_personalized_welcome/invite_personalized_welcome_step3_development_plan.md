1. Persist invite personalization data
   - Dependencies: new SQLModel table allowed; reuse existing invite creation pipeline.
   - Changes: add `InvitePersonalization` model keyed by invite token; extend `auth_service.create_invite_token` to store required fields and expose them in API responses; update `/auth/invites` route validation to enforce required strings and minimum help example count.
   - Testing: unit-by-inspection (Python not available) plus manual API call via DevTools; confirm stored payload retrieved with invite.
   - Risks: exceeding storage limits or missing data on registration; mitigate with strict length caps and error handling if persistence fails.

2. Upgrade "Send welcome" form UI and client logic
   - Dependencies: Stage 1 fields defined in API response.
   - Changes: redesign `templates/invite/new.html` to require username, photo URL, gratitude note, support promise, multiple help examples, and fun details; enforce client-side validation and adjust share preview rendering; surface inline guidance about tone and limits.
   - Testing: manual form submission with valid/invalid data; ensure preview strings reflect input and invite regeneration reuses last entries.
   - Risks: UX regressions on small screens; keep layout within existing card/container patterns.

3. Enhance registration experience
   - Dependencies: Stage 1 decode helper.
   - Changes: update `/register` view to parse invite personalization payload and pass structured data to template; extend `templates/auth/register.html` to show photo, gratitude/support/help/fun sections, while retaining form fields; ensure fallback when personalization missing.
   - Testing: manual navigation via invite link with/from without personalization.
   - Risks: Template errors when data absent; guard with defaults.

4. Verification sweep
   - Dependencies: prior stages complete.
   - Changes: document testing status in Step 4 summary.
   - Testing: manual smoke — generate invite, copy link, visit register page; attempt invalid submissions; note automated test gaps.
   - Risks: forgetting to cover non-admin access; confirm access control still enforces admin-only creation.
