Problem: New invitees receive minimal context when joining, making the welcome feel generic and requiring extra effort to set up their profile.

User stories:
- As an inviter, I want to preload my friend’s signup with a username, photo, and personal notes so they feel seen when they arrive.
- As an invitee, I want to land on the registration page with thoughtful details already filled in so I know why I was invited and how my friend can support me.
- As an administrator, I want standardized invite requirements so every welcome includes helpful information for community moderators.

Core requirements:
- Make the "Send welcome" form require a suggested username, photo link, gratitude note, support message, and a brief fun/inside-joke section.
- Require the inviter to list at least two concrete ways they can help (e.g., groceries, rides) before generating an invite link.
- Persist the personalization data with the invite token so the registration page can render the warm welcome details and the share preview message includes them.
- Keep existing invite generation flow (links, QR codes) intact.

User flow:
1. Inviter opens the "Send welcome" page from the dashboard.
2. They complete required fields: username, photo URL, gratitude note, support promise plus at least two help examples, and fun facts/inside jokes.
3. They generate the invite link; the confirmation view shows the share message and QR code including the new personalized content.
4. Invitee follows the link, sees their prefilled username and the personalized welcome details, and finishes signup.

Success criteria:
- Invite creation fails with clear guidance if required personalization fields are missing or too short.
- Generated invites store and expose the personalization payload so the registration page renders all sections and the share-preview text reflects them.
- Existing invite token behavior (QR/link, max uses) continues to work without regression in manual smoke tests.
