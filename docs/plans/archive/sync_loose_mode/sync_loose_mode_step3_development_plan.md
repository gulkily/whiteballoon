## Stage 1 – Config flags & plumbing
- Goal: Extend hub config (`app/hub/config.py`) to recognize `allow_auto_register_push` / `allow_auto_register_pull` (default false).
- Changes: Parsing, dataclass fields, settings object; update docs to mention new flags.
- Verification: Hub starts with/without flags; `GET /api` unaffected.
- Risks: None.

## Stage 2 – CLI public key header
- Goal: Have `wb sync push/pull` include the local public key when talking to hub peers.
- Changes: In `tools/dev.py`, compute `ensure_local_keypair(auto_generate=True)` and send header `X-WB-Public-Key` on HTTP requests.
- Verification: Inspect hub logs to confirm header arrives; existing filesystem peers unaffected.
- Risks: Minimal; ensure header only sent for hub peers.

## Stage 3 – Push auto-registration
- Goal: If `allow_auto_register_push` and peer unknown, hub creates entry on upload.
- Changes: Modify `upload_bundle` handler to detect unknown peers, read token hash + public key (from header), persist to config (append + reload), then proceed with signature verification/storage.
- Verification: With flag on, first-time push succeeds and peer appears in config; flag off still returns 404.
- Risks: Concurrent writes to config file; mitigate with simple file lock (optional) or atomic rewrite.

## Stage 4 – Pull auto-registration
- Goal: Similar for downloads: when flag enabled, allow unknown peers by verifying manifest signature with the supplied public key and persisting the entry.
- Changes: `download_bundle` handler reads header, auto-creates peer if allowed before serving bundle; include warning if no bundle yet.
- Verification: Fresh peer can pull with flag on; strict mode unchanged.
- Risks: Serving bundle to unverified peers if signature check skipped—ensure we verify `bundle.sig` using provided key before storing/serving.

## Stage 5 – Responses & auditing
- Goal: Include `auto_registered: true/false` in push/pull JSON responses and log events for admins.
- Changes: Adjust API payloads; optionally append to a lightweight log file for review.
- Verification: Trigger auto-registration and confirm response/log entries.
- Risks: None.

## Stage 6 – Docs & UI note
- Goal: Document loose-mode flags in `docs/hub/README.md`/INSTALL guides; mention CLI auto-header.
- Changes: README updates, quickstart snippet.
- Verification: Docs mention new workflow.
- Risks: None.
