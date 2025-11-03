1. Expose creator metadata in request payloads  
   - Dependencies: existing `HelpRequest` records include `created_by_user_id`; no schema changes.  
   - Changes: extend `RequestResponse` to carry `created_by_username`; update `_serialize_requests` and API routes to hydrate usernames via a single query per batch; ensure half-auth and full-auth flows receive the new field.  
   - Testing: manual check via `/api/requests` response in browser or CLI; verify hydrated usernames for existing and new requests.  
   - Risks: missing usernames for legacy rows; mitigate with safe fallbacks when lookup fails.

2. Render creator name in server-rendered request cards  
   - Dependencies: Stage 1 provides `created_by_username`.  
   - Changes: update `templates/requests/partials/item.html` to show the creator name at the top-left of each card with a fallback label; adjust surrounding markup to keep badge/time aligned.  
   - Testing: manual load of requests dashboard (full auth) and pending view (half auth) to confirm layout and fallback text.  
   - Risks: layout regressions on small screens; minimize by keeping markup lightweight and relying on existing utility classes.

3. Update client-side request feed rendering and styles  
   - Dependencies: Stage 1 field availability.  
   - Changes: adjust `static/js/request-feed.js` to render the creator name when cards are refreshed dynamically; add minimal CSS supporting the name placement (e.g., spacing, typography).  
   - Testing: trigger a request submission flow to confirm the live-updated card shows the name and that styling matches server-rendered version.  
   - Risks: inconsistent markup between server and client templates; address by mirroring structure exactly.

4. Verification and regression sweep  
   - Dependencies: prior stages complete.  
   - Changes: none (execution step).  
   - Testing: manual smoke — create request as half-auth and full-auth users, confirm dashboards display creator names consistently; verify API still returns expected fields and completion actions unaffected.  
   - Risks: overlooking edge cases such as requests without `created_by_user_id`; confirm fallback text renders and log console free of errors.
