Problem: Members viewing the main requests dashboard cannot tell who submitted each request, creating friction for follow-up and moderation.

User stories:
- As an administrator, I want to see who created each request so that I can reach out or moderate quickly.
- As a fully authenticated member, I want to know who posted a request so that I can coordinate directly if needed.
- As a half-authenticated member, I want visibility into who shared a request so that I can build trust with the community.

Core requirements:
- Show the request creator’s display name or username on every request card in the main dashboard.
- Ensure the name is visible to all signed-in users, regardless of authentication level or admin status.
- Place the name in the upper-left area of the card, consistent across desktop and mobile layouts.

User flow:
1. User signs in (half-authenticated or fully authenticated) and reaches the main requests dashboard.
2. The dashboard loads existing requests.
3. Each request card displays its status badge, creator name, timestamp, and description.
4. User can scan cards and immediately identify who created each request.

Success criteria:
- Request cards on the main dashboard consistently show the creator name without layout regressions.
- Half-authenticated, fully authenticated, and admin users all see the same creator name.
- No regressions in request loading or completion actions are observed in manual smoke tests.
