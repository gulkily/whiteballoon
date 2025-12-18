# AI Chat Query – Step 2: Feature Description

**Problem**: Members and operators spend time remembering CLI commands, filters, and dashboards just to retrieve routine facts. We need a conversational AI surface that lets them ask natural-language questions and receive sourced answers drawn from existing Whiteballoon data.

## User stories
- As a request steward, I want to ask “Who followed up on the Rivera housing request this week?” so that I can quickly see accountable owners without combining multiple exports.
- As a network connector, I want to ask “Show me mutual contacts who recently offered AI tutoring” so that I can route inquiries without re-running filtered searches.
- As an operations lead, I want to ask “What are the top topics in unread chats today?” so that I can prioritize moderation and support work.

## Core requirements
- Accept plain-language prompts through a chat UI and maintain short conversational context (follow-up questions without restating filters).
- Responses must cite the underlying objects (request IDs, chat messages, docs) so users can verify and click through.
- Respect existing auth scopes and data-visibility rules when retrieving results.
- Provide graceful failure/guardrails when the system lacks sufficient context or the query is out of scope.
- Log questions/answers for auditing and future tuning without recording sensitive plaintext beyond current policies.

## Shared component inventory
- `wb chat` CLI shell: extend with an `ai` sub-mode so members can launch conversational queries without leaving terminal workflows; reuse existing session/auth plumbing.
- Web “Chats” page (React component in `app/static/js/chat`): embed the AI panel alongside recent threads to keep context continuity; reuse message list styling for transcripts.
- Retrieval backend (`dedalus` embedding + FastAPI `/chat/respond`): extend to support multi-document RAG plus citation metadata rather than building a new microservice.
Each surface should reuse canonical chat bubble styles and the shared retrieval API to avoid diverging UX or data contract forks.

## Simple user flow
1. User opens CLI (`wb chat ai`) or the chats page and sees an “Ask AI” input with guidance text.
2. User submits a question; the client calls the shared AI chat endpoint with user context and conversation ID.
3. Backend runs retrieval over indexed requests/chats/docs, composes the prompt, and generates a cited answer.
4. Client renders the response with citations that deep-link back to the referenced records.
5. User optionally asks a follow-up within the same conversation, reusing context with truncated history.
6. User copies cited commands/links or exits the chat; conversation metadata is logged for metrics.

## Success criteria
- ≥80% of pilot users report they “got the information they needed” via the AI chat in weekly feedback surveys.
- Median response latency (client send → first token) stays under 4 seconds for typical retrieval scopes.
- ≥70% of answers include at least one working citation link back to Whiteballoon data.
- Logged usage shows at least 30 distinct users running ≥3 queries each within the first month of release.
