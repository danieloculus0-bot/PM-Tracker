# Windows Server installation (generic release)

This guide covers a **blank**, generic PM Tracker server installation. It does **not** migrate, publish, or restore any existing maintenance records. Only synthetic data may enter this public repository, GitHub Actions, or its release artifacts.

## Before installation

- Use an x64 Windows Server host with administrative rights, PowerShell and the relevant local firewall policy. No separate Python installation is required for the packaged executable.
- Obtain the **Build Generic Windows Server Release** artifact from the [GitHub Actions workflow](https://github.com/danieloculus0-bot/PM-Tracker/actions/workflows/windows-server-release.yml), selecting the latest **successful run on main**. The release ZIP contains an executable and scripts; the separate setup executable is also in the artifact.
- Compare the SHA256 hash of the installer or ZIP with the accompanying `SHA256SUMS.txt`. For example:

  ```powershell
  Get-FileHash '.\PM-Tracker-Server-Setup.exe' -Algorithm SHA256
  Get-Content '.\SHA256SUMS.txt'
  ```

- Arrange for internal network access only. The generic example binds to `0.0.0.0:5000`; the install script creates a Windows inbound rule for **Domain** and **Private** profiles. There is no application user-login system, TLS termination, or reverse proxy in this bundle.
- An upgrade to an existing installation requires a verified **offline backup** of `pm_app.db`, `pm_data.xlsx`, and `site_config.json` first. Stop the running scheduled task before replacing the executable. Keep the backup off the public repository.

## Fresh blank install

1. On the Windows Server machine, run `PM-Tracker-Server-Setup.exe` as an administrator. The default installation folder is `C:\ProgramData\PM Tracker`.
2. The setup copies the packaged app and generic import template; if missing, it creates `site_config.json` from `site_config.example.json` and `pm_data.xlsx` from the blank template.
3. The install script registers a Windows Scheduled Task named `PM Tracker Server` to start at boot, run as `SYSTEM`, and use the installation directory as its **working directory**. Working directory matters: the app stores its SQLite database and workbook relative to the process current directory.
4. The scheduled task starts the Waitress HTTP server. The app initializes the blank SQLite database as needed.

Do not copy production data to this blank installation as part of the install or a GitHub action. Data migration is a distinct, separately approved operation.

## Post-install verification

From an elevated PowerShell session on the server:

```powershell
Get-ScheduledTask -TaskName 'PM Tracker Server' | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName 'PM Tracker Server' | Select-Object LastRunTime,LastTaskResult
Get-ChildItem 'C:\ProgramData\PM Tracker' -Name
Invoke-WebRequest 'http://127.0.0.1:5000/' -UseBasicParsing -TimeoutSec 10 | Select-Object StatusCode
```

Expected: task exists, the HTTP request returns `200`, and `pm_app.db` and `pm_data.xlsx` exist. A `200` only verifies local HTTP responsiveness; additionally verify a fictional machine/task can be entered and viewed in a **test instance** before real use. If you change the configured port, use that port instead of 5000 for verification. Windows task results alone are not a live-health guarantee.

For remote clients, use the server's authorized DNS name or internal IP and the configured port. Check the actual Windows network profile and site IT firewall policy if a localhost check works but remote access fails. Do **not** open the port to the internet.

## Configuration and operating notes

- Edit `C:\ProgramData\PM Tracker\site_config.json` **on the server**, not in GitHub. Configure `site_name`, weather settings, `host`, and `port` as needed. Restart the scheduled task to reload configuration; rerun `install-server.ps1` as administrator if the port changes so the firewall rule matches.
- This application uses **two distinct persistent stores**: `pm_data.xlsx` holds machine/task definition sheets and an optional imported completion log; `pm_app.db` (SQLite) holds operational completions and maintenance requests. They are **not interchangeable**.
- Back up both stores and the local configuration consistently, after stopping writes. Do not overwrite a database with an old EXE's test data. Importing a workbook is not a substitute for a complete database history migration.
- Keep machine-specific documents, original PM records, exports, hostname/site coordinates, server configuration, and logs outside GitHub.

## Updating an existing installation

1. Record the running version and stop the scheduled task with `Stop-ScheduledTask -TaskName 'PM Tracker Server'`.
2. Back up both runtime stores and the site configuration to a private, access-controlled location. Verify that the backup files are readable.
3. Run the new installer as administrator, keeping the original install directory.
4. Verify the startup task, localhost HTTP response, machine/task inventory, prior completions and maintenance requests.
5. If checks fail, stop the task, restore the previous executable and its matching data backup, then restart. Diagnose before accepting new updates.

The uninstaller removes the scheduled task and its firewall rules but is designed to preserve runtime data. Independently verify any backups before uninstalling.

## Deployment evidence boundary

The Windows GitHub Actions job compiles and packages a generic artifact. It is **not** proof of a real Windows Server installation, site permissions, reliability under concurrent users, data migration correctness, or external network policy. These must be checked on the actual target server.
