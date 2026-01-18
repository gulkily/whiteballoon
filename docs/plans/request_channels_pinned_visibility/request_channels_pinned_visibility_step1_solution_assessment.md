# Request Channels Pinned Visibility — Step 1 Solution Assessment

Problem statement: The /requests/channels UI can hide the pinned or active conversation behind filters, forcing a warning message and making it harder to reach the current thread.

Option A — Dedicated priority strip above filters
- Pros: Keeps pinned + active visible without changing filtered results; clear mental model; avoids confusing counts.
- Cons: Adds a second list area that may feel redundant; needs extra layout space.

Option B — Always-include pinned/active inside the filtered list
- Pros: Single list to scan; no extra layout block; preserves proximity to other channels.
- Cons: Filters become less trustworthy because exceptions are mixed in; count label needs special handling.

Option C — Conditional “priority” block only when exceptions exist
- Pros: Avoids extra UI most of the time; keeps filters pure when possible.
- Cons: UI shifts depending on state; still needs two list behaviors to explain.

Recommendation: Option A. A dedicated priority strip keeps filter logic clean, makes the pinned + active channels reliably reachable, and removes the need for the hidden-filter warning.
