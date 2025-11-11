# Ubuntu Deployment Guide – WhiteBalloon Sync Hub

This guide walks through installing the hub relay on Ubuntu 22.04+. Adjust paths/versions as needed.

## 1. Install prerequisites
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

## 2. Create deployment user (optional but recommended)
```bash
sudo adduser --system --group wb-hub
sudo mkdir -p /opt/wb-hub
sudo chown wb-hub:wb-hub /opt/wb-hub
```

## 3. Clone the repo and set up a virtualenv
```bash
sudo -u wb-hub bash -lc '
  cd /opt/wb-hub && \
  git clone https://github.com/<your-org>/whiteballoon.git . && \
  python3 -m venv .venv && \
  source .venv/bin/activate && \
  pip install --upgrade pip && \
  pip install -e .
'
```

## 4. Configure the hub
Generate a config at `/opt/wb-hub/.sync/hub_config.json` (the service writes a stub automatically if missing). Example:
```json
{
  "storage_dir": "data/hub_store",
  "peers": [
    {
      "name": "alpha",
      "token": "super-secret-token",
      "public_key": "BASE64_ED25519"
    }
  ]
}
```
- `token`: bearer token each peer will present. Treat it like a password.
- `public_key`: base64 output from `./wb sync keygen` on the peer instance.
- Add one object per peer you want to accept uploads from.

## 5. Test run manually
```bash
sudo -u wb-hub bash -lc '
  cd /opt/wb-hub && \
  source .venv/bin/activate && \
  PYTHONPATH=. WB_HUB_CONFIG=.sync/hub_config.json python tools/hub.py
'
```
Open another terminal and verify `/api/v1/sync/<peer>/status` responds (use curl with the bearer token).

## 6. Create a systemd service
`/etc/systemd/system/wb-hub.service`:
```ini
[Unit]
Description=WhiteBalloon Sync Hub
After=network.target

[Service]
User=wb-hub
Group=wb-hub
WorkingDirectory=/opt/wb-hub
Environment=WB_HUB_CONFIG=/opt/wb-hub/.sync/hub_config.json
Environment=PYTHONPATH=/opt/wb-hub
ExecStart=/opt/wb-hub/.venv/bin/python tools/hub.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wb-hub.service
sudo systemctl status wb-hub.service
```

## 7. Add HTTPS (recommended)
Place the hub behind a reverse proxy (Caddy, Nginx, Traefik) that terminates TLS and forwards to `localhost:9100`. Example Nginx snippet:
```nginx
location /api/v1/sync/ {
    proxy_pass http://127.0.0.1:9100$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```
Use Let’s Encrypt (`certbot`) for certificates.

## 8. Rotating peers/tokens
- Update `.sync/hub_config.json` with new `token` or `public_key` entries.
- Reload the service: `sudo systemctl restart wb-hub`.
- Distribute the new token/base64 key to peer operators so their CLI can push/pull via `./wb sync peers add --url ... --token ...`.

## 9. Backups & monitoring
- Back up `data/hub_store/` (the stored bundles) and `.sync/hub_config.json` regularly.
- Watch logs: `journalctl -u wb-hub -f`.
- Consider adding fail2ban or rate limits if exposed publicly.

With the service running, peers can register the hub URL and token via:
```bash
./wb sync peers add --name hub --url https://hub.example --token <secret> --public-key <base64>
```
Then use `./wb sync push hub` / `./wb sync pull hub` as usual.
