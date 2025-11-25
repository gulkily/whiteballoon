## Problem
Signal chats imported as request comments hold critical commitments and context, but there is no way to search or surface relevant snippets when triaging new requests, so responders waste time scrolling or miss key details.

## User Stories
- As a dispatcher reviewing a request, I want to search within its imported Signal chat by person or keyword so I can quickly find the right context.
- As a responder planning follow-up work, I want relevant chat hits surfaced when a request mentions entities discussed earlier so I can reuse commitments or contacts.
- As an administrator auditing past actions, I want a direct link from a surfaced chat hit back to the original import so I can cite the precise message.

## Core Requirements
- Provide scoped search over the Signal comment thread attached to a request, including filtering by keyword and participant name.
- Display search results inline on the request page, highlighting matched terms and linking to the exact comment anchor.
- Automatically reindex imported chats when new messages are appended to ensure search freshness.
- Offer optional “Related chat mentions” suggestions on other requests by matching shared names/topics via simple heuristics (prereq for later automation).

## User Flow
1. Dispatcher opens a request with an imported Signal chat.
2. Dispatcher types a keyword or name into the new “Search chat” input.
3. System queries the chat index and shows matching comments with highlights and anchors.
4. Dispatcher clicks a result to jump to that comment or copy a link/reference into their notes.
5. When viewing a different request with overlapping entities, the system lists top related chat snippets as suggestions.

## Success Criteria
- 90% of chat-related lookups completed without manual scrolling through the raw thread.
- Search results return in <500 ms for chats up to 5,000 messages.
- Suggested related snippets appear on at least one other request per imported chat when overlapping names exist.
- Dispatchers report (via qualitative feedback) that finding prior promises is “easy” or “very easy.”
