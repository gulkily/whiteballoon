# Profile Comments Titles – Step 3 Development Plan

## Stage 1 – Grouping logic + template update
- **Goal**: Render grouping headers per request on `/people/{username}/comments`.
- **Dependencies**: Existing `profile_comments` route and template.
- **Changes**: Update the route to annotate each serialized comment with a boolean when the request changes (has_new_header). Adjust the template to emit a heading/summary for that group and move the request link/title into the header.
- **Verification**: Create seed data with mixed requests, load comments page, confirm only one heading per request on a page; ensure pagination boundaries still show headings as expected.
- **Risks**: Wrong grouping when consecutive comments share IDs across page boundaries; need to ensure headers show even when the first comment on a page is a continuation.

## Stage 2 – Styling polish + README blurb (optional)
- **Goal**: Tweak CSS for headers and confirm documentation mention.
- **Dependencies**: Stage 1 markup done.
- **Changes**: Add small styles for group headings and update README profile note if behavior change is notable.
- **Verification**: Manual visual check; confirm docs mention “grouped by request” if needed.
- **Risks**: Minimal.
