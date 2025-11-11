# WhiteBalloon Sync Hub

The sync hub is a lightweight FastAPI service that relays signed `data/public_sync` bundles between instances. It lives inside this repo (`app/hub/`) so it can reuse the existing signing utilities.

## Configuration

1. Launching the hub for the first time generates a sample config:
   ```bash
   WB_HUB_CONFIG=.sync/hub_config.json python tools/hub.py
   ```
   If `.sync/hub_config.json` is missing, the process writes a stub and exits.
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
WB_HUB_CONFIG=.sync/hub_config.json python tools/hub.py
```
- Default port: `9100` (adjust by wrapping with uvicorn CLI if needed).
- Endpoints:
  - `POST /api/v1/sync/<peer>/bundle` — upload tar.gz of `data/public_sync` (requires bearer token).
  - `GET /api/v1/sync/<peer>/bundle` — download the latest bundle (token required).
  - `GET /api/v1/sync/<peer>/status` — retrieve metadata (digest, timestamps, file counts).

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
   The CLI detects `--url` and uses the hub endpoints automatically. Signature verification still runs locally, so leaked bundles remain tamper-evident.

## Notes
- Hub never alters bundle contents; it only validates signatures and stores the uploaded files verbatim.
- Public keys in `data/public_sync/public_keys/` travel with each bundle, allowing new peers to bootstrap trust.
- Front the hub with TLS (Caddy/NGINX) and rotate tokens periodically. For multi-tenant deployments, consider moving peer config into a database.
