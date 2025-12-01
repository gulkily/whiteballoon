# Session CLI – Feature Description

- **Problem**: Administrators currently must use the web UI to inspect and approve pending login requests; we need CLI commands in `./wb` to manage sessions quickly from the terminal.
- **User stories**:
  - As an admin, I want to list pending authentication requests so I can see who’s awaiting approval without opening the browser.
  - As an admin, I want to approve or deny a pending request via CLI so I can unblock trusted users faster.
  - As a developer, I want a consistent Typer interface that surfaces session metadata (user, code, created time) for scripting/auditing.
- **Core requirements**:
  - Add Typer subcommands (e.g., `wb session list`, `wb session approve <id> [--code ...]`) that query `AuthenticationRequest` + related session/user data.
  - Display useful fields: request ID, username, created time, status, verification code.
  - Approve command should mark the request as approved, promote pending requests (`status = 'open'`), and output success/error.
  - Deny/cleanup command (optional) should mark requests as denied or expired.
  - Commands should read from existing config/env without extra setup.
- **User flow**:
  1. Admin runs `./wb session list` → sees pending requests with IDs/codes.
  2. Admin runs `./wb session approve <request_id>` (optionally passing approver username) → CLI reports success and promotion actions.
  3. (Optional) Admin runs `./wb session deny <request_id>` to decline a request.
- **Success criteria**:
  - CLI commands list and approve sessions reliably, updating DB status and promoting pending requests.
  - Output is human-readable (tables or simple columns) and script-friendly.
  - Documentation (`docs/spec.md`, README, cheat sheet) mentions the new commands.
