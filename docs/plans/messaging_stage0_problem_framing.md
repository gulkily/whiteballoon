# Messaging Stage 0 – Problem Framing

## Problem statement
WhiteBalloon members currently have no way to send private, asynchronous messages to one another in-app—coordination happens either via public request comments or by jumping to external tools after someone shares contact details. This breaks the trust graph we are cultivating, makes follow-up on requests brittle, and prevents the AI layer from seeing the intent signals that emerge once two people begin working together. We need a minimal, auditable messaging surface that lets any authenticated member send and receive direct messages while preserving the existing permissions model.

## Current pain points
- Request comment threads are tied to a single help request and visible to many parties, so members avoid discussing sensitive or logistical details there.
- Without first-party messaging, members drop into Signal/Telegram/iMessage, creating fragmented histories and no reliable audit trail for abuse handling.
- Operators cannot tell whether introductions the AI suggests actually led to conversations, so we cannot measure if trust-driven matching is effective.

## Success metrics
- ≥70% of one-to-one follow-ups that originate from a request or profile view stay inside WhiteBalloon within 30 days of launch (tracked via conversation creation events).
- Median message send-to-receive latency stays under 2 seconds for 95% of deliveries during manual tests on a 1000-message synthetic dataset.
- Moderators can export a member’s conversation history (limited to permitted scopes) in ≤1 minute for abuse reviews, demonstrating we have auditable, retrievable logs.

## Guardrails
- Scope: “basic messaging” means text-only, one-to-one threads between authenticated human-operated accounts—no attachments, reactions, or group chats in this iteration.
- Data isolation: store the messaging tables in a dedicated SQLite database file so we can experiment with retention policies, future sharding, or encryption-at-rest without risking the primary app DB.
- Privacy & policy: reuse existing membership permissions—only mutually visible members (per directory rules) can initiate messages, and we must log moderation metadata for compliance.
- Delivery mechanism: prioritize durability over push sophistication; background tasks and web polling are acceptable, but we should not introduce new third-party services in Stage 0.
