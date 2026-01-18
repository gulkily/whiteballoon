# Request Channel Presence Ping Dedupe — Step 2 Feature Description

Problem: Request channel presence updates are sent by every open tab, causing redundant pings and unnecessary server load. The feature should reduce duplicate pings while keeping presence and typing indicators accurate in all tabs.

User stories:
- As a signed-in user with multiple tabs open, I want presence pings to be deduped so that the system is not overloaded by my session.
- As a request channel participant, I want online and typing indicators to stay accurate even when I have several tabs open.
- As an operator, I want presence traffic to stay bounded per user so that the service remains responsive.

Core requirements:
- Presence pings are limited to one per interval per user across tabs for the request channels UI.
- Presence and typing indicators continue to update reliably in every open tab.
- The experience degrades gracefully if cross-tab coordination is unavailable.
- No new UI surfaces are introduced; existing indicators remain the source of truth.

Shared component inventory:
- Request channels list presence badge: reuse existing markup in `templates/requests/channels.html` and rendering logic in `static/js/request-channels.js`.
- Channel chat typing indicator: reuse existing markup in `templates/requests/partials/channel_chat.html` and rendering logic in `static/js/request-channels.js`.
- Presence API endpoints: reuse `/requests/channels/presence` GET/POST without new routes.

Simple user flow:
1. User opens two or more request channel tabs.
2. The UI coordinates to ensure only one tab sends the periodic presence ping.
3. All tabs continue to display online counts and typing indicators.
4. If a tab is closed, another tab maintains the periodic ping without user action.

Success criteria:
- With multiple tabs open, server logs show no more than one presence ping per interval per user session.
- Presence and typing indicators stay current across tabs with no visible regression.
- No new UI elements or settings are required for users.
