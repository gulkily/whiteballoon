## Problem
The “Mark completed” control appears on every open request card, even when the signed-in user did not create that request. This misleads helpers into thinking they can complete requests they do not own and results in unnecessary 403 responses from the backend.

## User stories
- As a request creator, I want to mark my own requests completed so that I can signal when the need is met.
- As a community helper viewing others’ requests, I want to avoid seeing unavailable actions so that I am not confused by controls I cannot use.
- As an administrator, I want to retain the ability to complete any request so that I can help close out stale or resolved items.

## Core requirements
- Hide or disable the completion action for requests that the current user neither created nor can administratively manage.
- Preserve the completion action for the request owner, regardless of full or half authentication state.
- Keep the admin override path intact and visually obvious when applicable.
- Ensure the request feed API exposes enough context to determine ownership without revealing unnecessary personal data.

## User flow
1. User signs in and lands on the request feed.
2. Each request card renders with context about ownership/permissions.
3. Eligible users (owner or admin) see the “Mark completed” button; others see no completion control.
4. Eligible users submit the completion form and the request transitions to the completed state.

## Success criteria
- Non-owners never see a completion control on open requests in the UI.
- Request owners (including half-authenticated owners viewing the public feed) continue to see and use “Mark completed.”
- Admin users continue to see and use “Mark completed” for any open request.
- Manual verification confirms that unauthorized completion attempts route is only reachable by direct request and still responds with HTTP 403.
