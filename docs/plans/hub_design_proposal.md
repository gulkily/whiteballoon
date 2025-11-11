
## Hub Design Proposal

### Goals
Enable NAT-constrained nodes to exchange signed bundles without manual shared folders by relaying through a reachable hub that validates and republishes bundles.

### Responsibilities
- Accept authenticated bundle uploads, verify signatures, and store artifacts per peer.
- Serve the latest bundle (manifest + signature + public key directory) to authorized peers.
- Track metadata (last push digest/timestamp) and expose status endpoints.
- Optional: centralize vouch records / peer discovery for future phases.

### Data Flow
1. **Push**: `wb sync push --hub <name>` signs the local bundle and POSTs it to `/api/v1/sync/<peer>/bundle` with a bearer token. Hub verifies signature using the peer’s registered public key and stores files under `storage/<peer>/`.
2. **Pull**: `wb sync pull --hub <name>` downloads the stored bundle via GET, verifies the signature locally (still required), then imports.
3. **Status**: CLI or UI hits `/api/v1/sync/<peer>/status` to fetch metadata (signed_at, manifest digest, file count).

### Hub Data Model
- `peers`: `{name, token_hash, public_key_b64, last_push_at, last_manifest_digest, bundle_path}`.
- `bundle_events`: audit log per upload/download.
- File storage mirrors current bundle layout plus `bundle.sig` and `public_keys/` directory.

### Security
- Issue random bearer tokens per peer; store hashed tokens server-side.
- Enforce signature verification before accepting uploads.
- Rate-limit endpoints and enforce bundle size caps.
- Optionally support mutual TLS later.

### CLI/Payload Changes
- `wb sync peers add` gains `--url` and `--token`; CLI distinguishes filesystem vs hub peers.
- `wb sync push/pull` detect peer type: filesystem copy vs HTTPS upload/download (with retries and checksum verification).
- Reuse `app/sync/signing.verify_bundle_signature` on both hub and client.

### API Sketch
- `POST /api/v1/sync/<peer>/bundle` – multipart upload (`manifest.sync.txt`, `bundle.sig`, tarball or individual files). Auth: `Authorization: Bearer <token>`.
- `GET /api/v1/sync/<peer>/bundle` – streams zip/tar or JSON manifest listing + signed files.
- `GET /api/v1/sync/<peer>/status` – returns metadata (digest, signed_at, file counts).
- Future: `GET /api/v1/peers` (discovery), `POST /api/v1/vouches` if the hub mediates vouch graph updates.

### Implementation Notes
- Hub can live as a small FastAPI app (either new service or module within WhiteBalloon).
- Storage: local disk or S3-compatible bucket; keep deterministic paths for git mirroring if desired.
- Start with single-tenant hub relaying bundles; extend to multi-peer fan-out later.


