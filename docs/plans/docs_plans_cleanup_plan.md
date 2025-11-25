# Docs/Plans Directory Cleanup Plan

## Goals
- Make `docs/plans/` easy to navigate by grouping files per feature and removing stale artifacts.
- Introduce consistent naming + index so contributors can find the right step documents quickly.

## Proposed steps
1. **Inventory current files**
   - List every entry under `docs/plans/`, capture which feature/initiative it belongs to, and flag orphaned drafts.
2. **Define structure**
   - Group documents by feature slug (existing naming already hints, e.g., `profile_comments_*`).
   - Add lightweight README/index in `docs/plans/` explaining the convention and linking to active features.
3. **Move/archive**
   - Create subfolders per feature when there are ≥4 related files; otherwise keep flat but ensure filenames stay consistent.
   - Move obsolete drafts (superseded or canceled) into `docs/plans/archive/` with a short note.
4. **Update references**
   - Search repo for links to moved files and update paths.
   - Mention the new structure in the main README or contributor docs.
5. **Enforce**
   - Add a short checklist (maybe in `FEATURE_DEVELOPMENT_PROCESS.md`) reminding folks to use the new layout when creating Step files.

## Open questions
- Do we need versioning for historical plan sets?
No.
- Should multi-stage initiatives get their own folder even if only a couple files yet?
Yes.