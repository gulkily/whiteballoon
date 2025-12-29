# Consistent Display Names – Step 3: Development Plan

1. **Catalog username render locations**  
   - Dependencies: Step 2 inventory draft.  
   - Expected changes: confirm/expand the template list by searching for `@{{` and other username patterns; document final list inside the Step 4 summary stub.  
   - Verification: cross-check against known pages (/requests/ID, /members, /browse, /peer-auth, /admin) to ensure no omissions.  
   - Risks: missing a template that builds usernames via JS or macros; mitigated by code search + manual walkthrough.  
   - Components touched: none (planning artifact only).  

2. **Add shared display-name component**  
   - Dependencies: Stage 1 list so we know the required props/states.  
   - Expected changes: create `templates/partials/display_name.html` (or a Jinja macro) accepting `username`, `display_name`, `href`, `class`, and `icon`. Document usage in `DEV_CHEATSHEET.md`.  
   - Verification: render component in isolation via template unit (e.g., include on a sample page) to ensure fallbacks and links work.  
   - Risks: macros unavailable in certain contexts; ensure includes work for both HTML partials and string-based templates.  
   - Components touched: new partial, helper doc.  

3. **Expose request-level display names**  
   - Dependencies: Stage 2 component shapes, existing `_load_signal_display_names` helper.  
   - Expected changes: extend `_build_request_detail_context` and `RequestResponse` serializer to include `created_by_display_name`, leveraging the same attr key used for comments; ensure JSON APIs do not leak unnecessary data.  
   - Verification: load `/requests/{id}` for Signal-imported and non-Signal requests to confirm context values populate.  
   - Risks: attr lookup may miss non-Signal users; acceptable fallback to usernames.  
   - Components touched: `app/routes/ui/__init__.py`, `app/modules/requests/routes.py`.  

4. **Replace inline username markup on request-related templates**  
   - Dependencies: Stage 2 component, Stage 3 data.  
   - Expected changes: update `templates/requests/detail.html`, `templates/requests/partials/item.html`, promoted comment blocks, request cards, etc., to include the shared component.  
   - Verification: manual checks on `/requests/30`, `/requests/39`, request feeds, and promoted-comment sections.  
   - Risks: class regressions if we remove existing wrappers; keep CSS hooks.  
   - Components touched: request templates, CSS if needed.  

5. **Update global/shared templates**  
   - Dependencies: Stage 2 component available.  
   - Expected changes: replace raw `@{{ username }}` occurrences in `partials/comment_card.html`, `partials/account_nav.html`, `members/index.html`, `browse/index.html`, `peer_auth/partials/list.html`, `admin/ledger.html`, `admin/profiles.html`, `invite/map.html`, `sync/public.html`, etc., using the component.  
   - Verification: spot-check key pages (Members, Browse, Peer Auth queue, Admin ledger) to ensure names render consistently and links still work.  
   - Risks: missing JS-rendered usernames; call out any follow-up needed for front-end scripts.  
   - Components touched: assorted templates.  

6. **Document usage + regression sweep**  
   - Dependencies: Stages 1–5 complete.  
   - Expected changes: add a short section to `DEV_CHEATSHEET.md` or `FEATURE_DEVELOPMENT_PROCESS.md` referencing the new component; update Step 4 summary with the final template list checked.  
   - Verification: manual pass over targeted pages and confirm `rg '@{{'` only hits intentional contexts (e.g., macros).  
   - Risks: future templates bypass component; mitigated by documentation.  
   - Components touched: docs, linting checklist.  
