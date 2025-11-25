# WSL port binding fix (Windows 11 23H2)

Running WhiteBalloon inside WSL on Windows 11 23H2+ can expose a networking bug where:
- Windows browsers cannot reach `localhost` ports exposed from WSL (`wb runserver`, FastAPI dev server, etc.).
- Ports look busy inside WSL even after `wsl --shutdown`, leaving new binds stuck or unresponsive.

Microsoft traced the regression to Windows Host Network Service (HNS) and the WSL virtual switch failing to release bindings after suspend/resume or rapid VM restarts. Rolling back the OS is not required—you can reset the networking stack safely instead.

## Recovery steps
1. **Shut down every WSL distro.** From an elevated Command Prompt or PowerShell window:
   ```powershell
   wsl --shutdown
   ```
2. **Restart the Windows Host Network Service.** In the same elevated shell run:
   ```cmd
   net stop hns
   net start hns
   ```

Restarting HNS tears down and recreates the virtual switch plus the lightweight NAT that bridges Windows ↔ WSL. Once it comes back up you can re-open your WSL terminal, rerun `./wb runserver`, and Windows should be able to hit `http://127.0.0.1:8000` again.

If the issue recurs after a Windows update or sleep cycle, repeat the steps above. Consider filing feedback through the Windows Insider Hub so Microsoft can prioritize a permanent fix.
