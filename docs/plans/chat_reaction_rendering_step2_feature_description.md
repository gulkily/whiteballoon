# Chat Reaction Rendering – Step 2: Feature Description

**Problem**: Signal-imported chat messages embed raw “(Reactions: name emoji, …)” text inside the message body, cluttering the transcript and making it hard to read individual responses. We need to strip that noise while still acknowledging that reactions happened.

## User stories
- As a request steward reading a busy chat, I want reactions summarized succinctly so I can focus on the actual messages.
- As a moderator, I want to know that a reaction occurred without scrolling through a dozen names inline.
- As a developer, I want a deterministic way to detect and remove reaction blocks so front-end templates stay simple.

## Core requirements
- Detect the legacy “(Reactions: …)” suffix in message bodies and remove it from the primary text content.
- Compute a concise summary (e.g., “Reactions: ❤️ ×12, 😮 ×1”) and render it separately (likely in the chat metadata/footer).
- Handle messages without reactions untouched; do not break existing formatting or stored message text.
- Keep all parsing/summary logic deterministic and safe against malformed input (unknown emojis, unexpected separators).

## Shared component inventory
- `templates/requests/partials/channel_message.html` – current chat message renderer; extend it to optionally show the summary.
- `static/js/request-chat-search.js` / search template – may need to strip reaction text when showing excerpts.
- Chat data comes from the existing `chat.comments` payload; no API changes required, but the backend or template filter must expose the stripped body + summary.

## Simple user flow
1. Message body is loaded from storage and checked for the “(Reactions: …)” suffix.
2. If present, parser removes the suffix and builds a map `{emoji -> count}` (and optionally total).
3. Template renders the cleaned message text.
4. Beneath the message, a small line (e.g., `Reactions: ❤️ ×12, 😮 ×1`) appears; if no reactions, nothing extra shows.

## Success criteria
- Reaction blocks no longer appear inline in chats, channel previews, or search snippets.
- Messages that previously contained reaction blocks still display the correct main text.
- Reaction summaries appear on at least one reference page (/requests/channels) and match the counts from the legacy text.
- No support tickets complaining about missing information; moderators confirm the summary line is sufficient.
