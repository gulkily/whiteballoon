# Comment Insight Filter Fix Plan

1. **Inspect Insight Metadata Pipeline**
   - Add temporary logging or REPL inspection inside `_build_request_detail_context` to view `insights_lookup` for a problematic request (e.g., Request #30). Confirm the metadata keys (`resource_tags`, `request_tags`, `urgency`, `sentiment`) are populated and lowercased consistently with the query params (`insight_request`, etc.).
   - Verify `comment_llm_analyses` holds entries for comments counted in the insight summary; if the summary is built from a different source, align `_build_comment_insights_lookup` with the summary data.

2. **Align Summary Chips and Filters**
   - Ensure `comment_insights_summary` and `_build_comment_insights_lookup` both consume the same tag data so badges like “Critical ×13” correspond to actual metadata attached to each comment. If needed, update `_record_tag_summary` or the summary builder to account for case sensitivity or alternate tag spellings.

3. **Adjust Filter Logic & Counts**
   - After confirming metadata alignment, review `_matches_insight_filters` to ensure it checks the correct sets for `resource`, `request`, `urgency`, and `sentiment`. Guard against missing metadata (return False only when a filter is active and the tag doesn’t match).
   - Update the footer/pagination text in `templates/requests/detail.html` to display filtered counts (use `comment_visible_count` when filters are active) so the UI doesn’t report the original total when only a subset is visible.

4. **Manual Verification**
   - Load `/requests/30?insight_request=onboarding` and `/requests/30?insight_urgency=critical` (or similar cases) after fixes. Ensure the comment list shows the expected number of entries and the footer reflects “Showing X of Y” correctly.
   - Repeat with no filters to confirm the original pagination behavior remains unchanged.
