# Half-Authenticated Restricted UI – Implementation Summary

## Overview
Implemented the restricted pending dashboard and draft experience for half-authenticated sessions while keeping initial pages server-rendered and progressively enhanced.

## Key Changes
- Added `templates/requests/pending.html` and updated `/` route logic to render three states (logged out, half, full) with SSR.
- Extended `static/js/request-feed.js` to manage collapsed form toggles, local draft storage, and read-only rendering for pending users.
- Adjusted request partials to respect a `readonly` flag so pending sessions cannot mutate community data.
- Hardened login flow to set session cookies correctly and display errors without relying on HTMX.
- Updated documentation/spec/README to describe the pending dashboard, draft behavior, and progressive-enhancement approach.

## Testing
- Manual flows: registration, login with pending state, verification, logout, request creation/completion before and after approval.
- Manual confirmation that drafts persist locally across refresh while awaiting approval and that they publish once fully approved.

## Follow-ups
- Shadow publish feature (server-side staging) planned separately.
- Consider automated coverage for login/pending flows in future test suite.
