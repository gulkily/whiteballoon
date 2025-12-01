Problem: Members browsing requests can’t jump from a requester’s name to their profile, slowing follow-up and community building.

User stories:
- As an administrator, I want to click a requester’s name and review their profile so I can confirm contact details before responding.
- As a member, I want to open the profile behind a request so I can learn more about the poster and coordinate support.
- As a half-authenticated member, I want consistent access to requester profiles so the dashboard feels trustworthy even before full approval.

Core requirements:
- Render each request creator name as a link that navigates to the requester’s profile view.
- Ensure all authenticated and half-authenticated sessions can reach the profile, with graceful handling when information is restricted.
- Maintain accessibility by using semantic links and preserving keyboard focus styles.

User flow:
1. Viewer lands on the requests dashboard and sees request cards with creator names.
2. Viewer clicks a creator name.
3. The app navigates to a profile page for that user, showing available details (or a friendly message if restricted).
4. Viewer can return to the dashboard using existing navigation.

Success criteria:
- Request cards include accessible links to creator profiles on both server-rendered and dynamically refreshed content.
- Navigating to another user’s profile succeeds for admins and members; half-auth viewers receive consistent messaging if access is limited.
- No new console errors or regressions in request creation/completion flows.
