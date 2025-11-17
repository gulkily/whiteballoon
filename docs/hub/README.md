# WhiteBalloon Sync Hub

The sync hub is a lightweight FastAPI service that relays signed `data/public_sync` bundles between instances. It lives inside this repo (`app/hub/`) so it can reuse the existing signing utilities.

## Configuration

1. Launching the hub for the first time generates a sample config:
   ```bash
   ./wb hub serve --config .sync/hub_config.json --host 127.0.0.1 --port 9100
   ```
   If `.sync/hub_config.json` is missing, the process writes a stub and continues with defaults. Flags you can add:
   - `"allow_auto_register_push": true` — let unknown peers register themselves on upload.
   - `"allow_auto_register_pull": true` — allow auto-registration during downloads.
2. Edit `.sync/hub_config.json`:
   ```json
   {
     "storage_dir": "data/hub_store",
     "peers": [
       {
         "name": "alpha",
         "token": "replace-with-secret",
         "public_key": "BASE64_ED25519_KEY"
       }
     ]
   }
   ```
   - `token`: the bearer token peers will send. Plain tokens are hashed internally; omit `token_hash` if you want the hub to hash it automatically.
   - `public_key`: base64 value printed by `./wb sync keygen` on the peer.
   - `storage_dir`: where bundles are persisted on the hub (ignored by git).

## Running the Hub

```
./wb hub serve --config .sync/hub_config.json --host 0.0.0.0 --port 9100
```
- Default port: `9100` (adjust by wrapping with uvicorn CLI if needed).
- Endpoints:
  - `POST /api/v1/sync/<peer>/bundle` — upload tar.gz of `data/public_sync` (requires bearer token).
  - `GET /api/v1/sync/<peer>/bundle` — download the latest bundle (token required).
  - `GET /api/v1/sync/<peer>/status` — retrieve metadata (digest, timestamps, file counts).

## Admin Dashboard

Generate an admin token (hashed into the config) with the CLI:

```bash
./wb hub admin-token --config .sync/hub_config.json --token-name ops
```

Restart the hub and visit `/admin`. Enter the printed token to view the dashboard, which surfaces:

- Config + storage locations and loose-mode flags.
- Per-peer bundle metadata (files, size, digest, last signed).
- A logout control that clears the admin session cookie.

Tokens are stored as SHA-256 hashes under `admin_tokens` in the config; rerun the command above to rotate them.
The CLI prints a 64-character hex string so it is easy to copy/paste or transcribe if needed.

### Pending Key Approvals

If a peer uploads a bundle signed by a public key that is not yet stored in the hub config, the upload now queues a pending approval:

1. Hub verifies the signature, captures the presented key, and stores the uploaded tarball under `data/hub_pending/<peer>/<entry-id>/`.
2. The client receives a `400` JSON payload with `{"error": "peer_key_mismatch", "pending_id": "..."}` so the operator knows an approval is required.
3. `/admin` shows a “Pending key approvals” table listing the peer, presented key, timestamps, and current key set. Clicking **Approve new key** appends the key to the peer’s allowed list, reloads the config, replays the stored bundle, and clears the pending entry. Discard simply deletes the queue entry.
4. Approved keys accumulate, so older keys remain valid until you remove them manually from `.sync/hub_config.json`.

This flow lets operators confirm a single dialog without editing JSON files or asking peers to retry uploads manually.

### CLI Pull Key Approvals

When a local instance pulls from a hub and the remote rotated signing keys, `wb sync pull <peer>` now caches the downloaded bundle and prints a pending approval message instead of crashing. Run `wb sync pull --approve <pending-id>` to trust the presented key (updates `sync_peers.txt`), import the cached bundle, and clean up. The `/admin/sync-control` pull log shows the same guidance so job reviewers know which pending ID to approve.

## Public Feed & Structured Store

The hub now renders a reddit-style feed at `/` backed by a lightweight SQLite database (`data/hub_feed.db`). Every bundle upload parses the `requests/*.sync.txt` files plus embedded comment transcripts and user exports, normalizes them into SQLModel tables, and surfaces the data to the UI and APIs.

- `GET /api/v1/feed/?limit=20&offset=0` returns paginated `HubFeedRequestDTO` objects with comment previews, counts, and manifest metadata. Skin builders can hit this endpoint directly for custom front-ends.
- The default SSR template shows ~20 most recent public requests with status pills, creator metadata, and the latest comments. A "Load more" button progressively enhances the page by calling the JSON endpoint.
- Only `Sync-Scope: public` entries are ingested, so keep private/pending records redacted before exporting bundles.

Skins can override the presentation layer without touching the ingest pipeline—simply reuse the JSON endpoint or extend the Jinja template.

## CLI Integration

On each WhiteBalloon instance:
1. Register the hub peer:
   ```bash
   ./wb sync peers add --name alpha --url https://hub.example --token <secret> --public-key <base64>
   ```
2. Push/pull:
   ```bash
   ./wb sync push alpha
   ./wb sync pull alpha
   ```
   The CLI detects `--url` and uses the hub endpoints automatically. It also sends the node's public key header so loose-mode hubs can auto-register peers. Signature verification still runs locally, so leaked bundles remain tamper-evident.

## Notes
- Hub never alters bundle contents; it only validates signatures and stores the uploaded files verbatim.
- Public keys in `data/public_sync/public_keys/` travel with each bundle, allowing new peers to bootstrap trust.
- Front the hub with TLS (Caddy/NGINX) and rotate tokens periodically. For multi-tenant deployments, consider moving peer config into a database.

See `docs/hub/INSTALL_UBUNTU.md` for a step-by-step deployment guide on Ubuntu (including systemd service wiring).
