# Request Chat Channels – Step 2 Feature Description

**Problem**: Reviewers juggle dozens of active requests and their comment threads; jumping between detail pages breaks the chat-like rhythm, slows triage, and hides unread updates.

**User Stories**
- As a reviewer, I want to see all active requests as channel rows with unread badges so that I can prioritize conversations at a glance.
- As a responder, I want to read and send comments in a continuous chat log so that context feels like Slack instead of paginated comment cards.
- As a lead, I want to pin or filter to priority requests while the chat pane stays open so that I can hop between channels without losing my place.
- As a collaborator, I want typing indicators and presence hints so that I know when teammates are actively engaging on a request.

**Core Requirements**
- Dual-pane layout with a request channel list (left) and chat log (right) sharing real-time state.
- Chat pane renders chronological comments with avatars, timestamps, and composer fixed to the bottom Slack-style.
- Channel rows show unread counts, priority indicators, and quick filter/search for request titles or participants.
- Deep links from legacy request detail URLs open the workspace with the matching channel focused.
- Presence + typing signals update in near real time while minimizing polling overhead.

**Shared Component Inventory**
- `RequestListTable` (request index view): reuse data provider + filter logic, but implement a new virtualized channel list presentation atop the same store.
- `RequestDetailHeader` (request detail banner): reuse summary chips (status, assignee) in the chat pane header to avoid forking metadata.
- `CommentCard` + `IdentityChip`: extend styles to support inline Slack-like bubbles while keeping avatar/name/time rendering consistent.
- `CommentComposer`: reuse composer logic (attachments, mentions) but wrap in new sticky bottom bar with live draft persistence.
- `RealtimePresenceStore`: extend existing presence service (used in chat search dialog) to broadcast typing/online signals for request channels.

**User Flow**
1. User opens Requests → “Channels” tab (or hits a deep link); workspace loads with their last active channel focused.
2. Left pane lists requests with unread badges, priority icons, and quick filter; user scrolls or searches to find a channel.
3. Selecting a channel updates the right chat pane, loading recent comments and anchoring to the newest message.
4. User reads the chat, sees presence/typing indicators, and uses the composer to add a comment; message appears instantly while server confirms.
5. User switches to another channel; left pane preserves search/filter state and right pane swaps to the selected chat without full-page reloads.

**Success Criteria**
- Switching between two requests shows the new chat log in <300 ms median without page reloads.
- Unread badge counts stay in sync with comment activity within 5 seconds of a new message.
- ≥90% of pilot reviewers report the workspace “matches Slack-style chat expectations” in feedback survey.
- Legacy request detail links reliably redirect into the workspace with the target channel focused (QA checklist passes for 20 sampled URLs).
