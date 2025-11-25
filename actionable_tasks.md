# Actionable Development Tasks

## Signal Chat Integration
1. Inventory the existing Signal chat(s) and export message history plus membership metadata; define the export cadence and secure storage pipeline.
2. Design a `signal_messages` schema that links each message to verified users, invite-tree relationships, resource categories, and contextual tags (ask/offers, urgency, location).
3. Build an ingestion job that parses the Signal export format, normalizes phone numbers, and upserts both members and conversations into the core database with idempotency safeguards.
4. Map imported requests/offers to platform-native request records so they appear in the feed and "ask for help" workflows; capture which ones still require manual classification.
5. Implement privacy controls so that only first-/second-degree users can view Signal-derived content, and build audit logs covering the entire import path.

## Information Distribution Feed
1. Implement connectors (scrapers/APIs) for mutual-aid directories and resource hubs; normalize into a `resources` table keyed by geography and assistance type.
2. Build a prioritization engine that filters to high-priority, community-relevant resources by matching against user-stated needs and trust circles.
3. Ship a personalized feed UI that shows ONLY vetted items from close contacts plus the high-priority external resources, with toggles for food, housing, funding, etc.

## Assisted Help Request Flow
1. Define the canonical list of pre-selected request templates (project help, referrals, rides, chores, emotional support, etc.) and localize them for mobile/desktop.
2. Implement a guided form wizard that forces template selection before any freeform text is allowed, captures date/time metadata, and supports "join me" style asks.
3. Add duplicate detection, moderation, and rate-limiting logic to eliminate troll/ spam requests (goal: block after 200 rejects).

## Funding + Warm Introduction Tools
1. Surface curated funding opportunities and warm-intro pathways inside the feed by tagging them as "funding" resources.
2. Build a lightweight workflow that lets a user request an intro to a funder, routes it through their inviter(s) for approval, and tracks acceptance/completion.

## Invite Tree & Network Visibility
1. Model invite relationships (who invited whom, timestamps) and store second/third-degree links for graph traversal queries.
2. Build an invite dashboard with filters for completed vs. open requests and toggles for 1st/2nd/3rd degree; require push notifications to be enabled for invitees.
3. Track repeat visits per user (goal: expose a badge when someone hits 10+ visits) to reinforce engagement metrics.

## Reference Letters & Access Control
1. Implement an invite-dependent onboarding gate that requires at least one reference letter; provide a friendly "not able to access" UI for ineligible users.
2. Create a one-click flow for existing members to vouch for someone, attach letters, and share them into third-party application forms when needed.
3. Enforce high-barrier rules (minimum number of vouches, manual review queue) before granting full platform access.

## Bulk Community Onboarding
1. Build CSV/phone-number list ingestion that lets an admin import an entire community, auto-tagging them as "member of community" with scoped permissions.
2. Provide progress/error reporting and a retry-safe import pipeline so large batches do not create duplicates.
