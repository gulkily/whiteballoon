# Signal Group Import – Step 1 Solution Assessment

**Problem statement**: Import the history of a specific Signal group chat into the local whiteballoon development environment (Windows host + WSL) so the data can seed database work before broader Signal integrations land.

## Options
- **Signal Desktop export on Windows + WSL handoff**
  - **Pros**: Fastest path; desktop app already logged into group, export delivers decrypted JSON/attachments; seamless file sharing via `\\wsl$` for ingestion scripts.
  - **Cons**: Requires local desktop client ownership of the group; manual re-export needed whenever messages change; desktop export still omits sender phone hashes so we must map contacts separately.
- **Android phone backup + `signal-back` restore inside WSL**
  - **Pros**: Provides full encrypted backup with phone-number metadata; repeatable using nightly Android backups; keeps Windows desktop untouched.
  - **Cons**: Needs root/USB debugging access and passphrase exchange; restore process inside WSL is slower and brittle on Windows file systems; entire account downloaded even if we only want one group.
- **Signal CLI headless join from WSL**
  - **Pros**: Automatable for future multi-chat ingestion; CLI can forward events directly into local DB without manual downloads; runs fully inside Linux tooling.
  - **Cons**: Requires registering a new Signal device/phone number; group admin must approve CLI device; setup effort high for “one group for now”.

## Recommendation
Pursue the **Signal Desktop export on Windows + WSL handoff** path to unblock the single-group import quickly. It needs only that the Windows Signal Desktop client exports the chosen group, after which we place the export in a shared folder (`C:\Users\<user>\Documents\signal_exports` mirrored into `/mnt/c/Users/...`) for parsing inside WSL. This minimizes new infrastructure, leverages an already-approved device, and keeps the scope aligned with importing just one group before scaling up.
