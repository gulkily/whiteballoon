# Testing the Hub Locally

Use this checklist to exercise the hub against your local WhiteBalloon instance.

## 1. Start the hub from the repo root
```bash
cd /path/to/whiteballoon
PYTHONPATH=. WB_HUB_CONFIG=.sync/hub_local.json python tools/hub.py
```
- On first run a sample config is written to `.sync/hub_local.json`; edit it so `peers` contains at least one entry:
  ```json
  {
    "storage_dir": "data/hub_store",
    "peers": [
      {
        "name": "local",
        "token": "test-token",
        "public_key": "<base64 from ./wb sync keygen>"
      }
    ]
  }
  ```

## 2. Register the hub peer in the CLI
```bash
./wb sync peers add --name local \
  --url http://127.0.0.1:9100 \
  --token test-token \
  --public-key <same base64>
```
(Use `./wb sync peers remove local` first if a filesystem peer already uses that name.)

## 3. Push and pull via the hub
```bash
./wb sync push local
./wb sync pull local
```
- `push` exports/signs `data/public_sync` and uploads it to `POST /api/v1/sync/local/bundle`.
- `pull` downloads `GET /api/v1/sync/local/bundle`, verifies `bundle.sig`, and imports the data.
- Watch the hub terminal for 202 responses to confirm uploads.

## 4. Inspect status endpoint (optional)
```bash
curl -H "Authorization: Bearer test-token" \
     http://127.0.0.1:9100/api/v1/sync/local/status
```
You should see `has_bundle: true`, along with manifest digest/timestamps.

That’s it—this setup mirrors what remote peers will do once the hub is hosted publicly, but everything stays on localhost for quick iteration.
