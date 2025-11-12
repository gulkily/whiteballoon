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
