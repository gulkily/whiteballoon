# Comment Card Alignment – Step 2 Feature Description

## Problem
Comment UIs still drift between contexts. Server-rendered lists, chat search results, and the JSON endpoint all return slightly different markup/data, making it hard to keep the UX consistent and causing regressions.

## User stories
- As an admin, I want every comment surface (requests, profiles, search) to show the same identity/timestamp/controls so I can rely on muscle memory.
- As a developer, I want a single partial/template that all comment surfaces reference, minimizing copy/paste markup.
- As a client/API consumer, I want the `/chat-search` JSON payload to include the same identity info so the JS experience matches the server fallback.

## Core requirements
1. Define a canonical `comment_card.html` partial that handles request, profile, and search variants (links, tooltips, actions) with predictable slots.
2. Update request detail list, profile comments, and both fallback + JS chat search to render that partial or clone its template.
3. Ensure `/requests/{id}/chat-search` JSON returns `display_name`, `comment_anchor`, and topic/tag metadata for each result.
4. Document the verification checklist: request comments, profile page, server fallback search (`?chat_q=`), JS search, and raw JSON endpoint.

## User flow
1. Server renders comments via the partial (request list, profile history, search fallback).
2. The chat search JS clones a `<template>` that matches the partial, injecting data from the JSON response.
3. Hitting `/requests/{id}/chat-search?q=foo` returns structured JSON with display names and anchors, so the UI or external tools display the same info.

## Success criteria
- All comment surfaces show matching identity/timestamp layout.
- Chat search looks identical whether JS is enabled or not.
- `/requests/{id}/chat-search` JSON includes the new fields and is documented.
- Plan steps are checked off with a final implementation summary.
