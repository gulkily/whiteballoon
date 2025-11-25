# Signal Group Export (Signal Desktop + signal-export CLI)

Workflow for exporting a single Signal Desktop group chat on Windows (with WSL) using the community `signal-export` tool. This replaces the old per-chat export UI, which Signal removed.

## Prerequisites
- Windows Signal Desktop already linked to the account that participates in the target group (membership required; no admin role needed).
- WSL distro (Ubuntu) with this repo under `/home/<user>/whiteballoon`.
- Python environment (either Windows or WSL) with `pip` available to install [`signal-export`](https://pypi.org/project/signal-export/).
- Full backup of the Signal Desktop data directory before touching it (`%APPDATA%/Signal` on Windows). Copy it somewhere safe, e.g., `C:\Users\<user>\Documents\signal_backup_before_export`.

## Install `signal-export`
1. Open a PowerShell prompt or WSL shell (either works; instructions assume WSL):
   ```bash
   pip install --upgrade signal-export
   ```
2. Verify installation:
   ```bash
   sigexport --help
   ```

## Obtain the Signal Desktop database key
Recent Signal builds encrypt the `sql/db.sqlite` database with a platform key. Follow the [`signal-export` README](https://github.com/carderne/signal-export#readme) for Windows:
1. Close Signal Desktop completely.
2. Copy `%APPDATA%/Signal` into your backup folder (this is critical in case anything corrupts).
3. Use the README’s PowerShell script to extract `Local State` secrets and decrypt the key. On Windows 10/11, this typically involves:
   ```powershell
   python -m sigexport.winutil --db-key
   ```
   The command prints the 64-character hex key needed for exports. Store it temporarily.
4. Re-open Signal Desktop if desired; the export tool only needs read access.

## List chats and find the group name
1. With the key in hand, point `sigexport` at the Signal Desktop data directory. From WSL:
   ```bash
   sigexport --db "'/mnt/c/Users/<user>/AppData/Roaming/Signal/sql/db.sqlite'" \
             --key "<64-char-hex-key>" \
             --list-chats
   ```
   (If running in Windows PowerShell, adjust paths accordingly.)
2. The command prints all chats. Copy the exact name of the group you want.

## Export the single group
1. Choose an output folder under the shared exports directory so WSL can read it, e.g., `C:\Users\<user>\sigexport\chats` (`/mnt/c/Users/<user>/sigexport/chats` in WSL).
2. Run the export (PowerShell example mirrors the command we used successfully):
   ```powershell
   python -m sigexport --chats "Exact Group Name" --source C:\Users\<user>\AppData\Roaming\Signal C:\Users\<user>\sigexport\chats
   ```
   From WSL, the same run looks like:
   ```bash
   sigexport --db /mnt/c/Users/<user>/AppData/Roaming/Signal/sql/db.sqlite \
             --key <64-char-hex-key> \
             --chats "Exact Group Name" \
             /mnt/c/Users/<user>/sigexport/chats
   ```
3. The tool writes:
   - `Exact Group Name.md` and `.html` (rendered chat)
   - `Exact Group Name.jsonl` (structured message data)
   - `attachments/` folder with media referenced in the chat

## Verification checklist
- [ ] Output directory contains the `.jsonl` file and attachments for the chosen group.
- [ ] Only the intended group appears (double-check file names).
- [ ] WSL can `ls /mnt/c/Users/<user>/sigexport/chats` without permission errors.
- [ ] Backup copy of `%APPDATA%/Signal` exists.

## Troubleshooting
- **`sigexport` cannot open DB**: Ensure Signal Desktop is closed or that you copied the DB elsewhere; Windows may lock the file.
- **Key mismatch**: Re-run `python -m sigexport.winutil --db-key`; make sure you paste the entire 64-char hex string without spaces.
- **Group not listed**: Confirm the desktop client belongs to the group; `--list-chats` output is case-sensitive.
- **Large attachments**: Export still succeeds but may take time. Keep the attachments folder since importer references it.

Once exported, use the resulting folder as the `--export-path` for `poetry run wb import-signal-group` when Stage 2 is implemented.
