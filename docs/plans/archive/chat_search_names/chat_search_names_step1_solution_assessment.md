# Chat Search Names – Step 1 Solution Assessment

**Problem statement**: Request detail pages show comment search results with `@username` links pointing back to the request, while the actual comment list displays friendly display names that jump to the commenter’s profile. The mismatch is confusing when Signal personas have aliases.

## Option A – Mirror comment list
- Pros: Consistent UI (display name with tooltip linking to profile) matches the comment list, reducing cognitive load.
- Cons: Requires extra data (display names) in the search response/template; profile link might surprise people expecting to jump within the request.

## Option B – Show both
- Pros: Combine display name + `@username`, giving full context and keeping the anchor inside the request.
- Cons: Clutters the result row; still inconsistent with the comment list layout.

## Option C – Keep username but add profile link
- Pros: Minimal change; just add a secondary link/button to open the profile while keeping the main anchor on the request.
- Cons: UI stays inconsistent and the extra link adds visual noise.

## Recommendation
Choose **Option A**. Update the search result entries to display the same avatar/name treatment used in the comment list (display name linking to `/people/<username>` with `@username` as a title attribute), while keeping the timestamp as the jump link to the specific comment in the request. This delivers consistent identity cues across the page.
