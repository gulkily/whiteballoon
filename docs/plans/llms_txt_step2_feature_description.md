# Step 2: Feature Description — /llms.txt for running instance

Problem: Agents lack a single, machine-readable entry point that reflects the live WhiteBalloon configuration, which makes engagement error-prone and inconsistent with human workflows.

User stories:
- As an agent, I want a `/llms.txt` summary of how to interact with this instance so that I can operate correctly without guessing routes or auth flow.
- As an agent operator, I want `/llms.txt` to reflect current settings and enabled modules so that agent guidance matches what the instance actually supports.
- As a human operator, I want agents to use the same public routes and permissions so that automated use is on equal footing with human users.
- As a developer, I want `/llms.txt` to point to existing documentation and APIs so that we avoid duplicating or drifting guidance.

Core requirements:
- `/llms.txt` is available at the instance root and can be fetched without special tooling.
- The content reflects current configuration (site title/base URL, enabled modules/feature flags, and relevant public entry points) at the time it is requested.
- Guidance references only the same public routes and authentication flows used by humans; no privileged or hidden endpoints.
- The file is concise, safe, and excludes secrets or private tokens.
- The file links/points to canonical docs and APIs already in the repo instead of re-defining them.

Shared component inventory:
- UI entry points (reuse): `/`, `/auth/login`, `/auth/register`, `/settings/account`, `/settings/notifications`, `/invite/new`, `/invite/map`, `/members`, `/people/{username}`, `/admin`, `/admin/sync-control`, `/sync/public`, `/sync/scope`, `/messages` (when enabled). `/llms.txt` should reference these rather than invent new flows.
- API surfaces (reuse): `/api/requests`, `/api/requests/pending`, `/auth/*`, `/feeds/<token>/<category>.xml` for RSS. `/llms.txt` should reference these as the programmatic surfaces.
- Documentation (reuse): `README.md` and `docs/spec.md` as canonical human-readable references; `/llms.txt` should point to them.
- New surface (new): `/llms.txt` itself as a machine-readable entry point because no existing UI/API surface provides this role.

Simple user flow:
1. Agent fetches `/llms.txt` from the running instance base URL.
2. Agent reads the instance metadata (title/base URL), enabled features, and the public routes/APIs it can use.
3. Agent follows the documented public auth and request flows to interact with the instance, using the same permissions as a human user.

Success criteria:
- Agents can fetch `/llms.txt` from a running instance and immediately identify the correct base URL, auth path, and public APIs.
- The content changes when operators change configuration (e.g., toggling messaging or skins) without manual edits.
- Operators confirm that no secrets or privileged instructions appear in `/llms.txt`.
- A basic agent task (read request feed or initiate auth) can be completed using only the information in `/llms.txt`.
