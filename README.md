# PM-Tracker

Standalone preventive maintenance scheduling, equipment tracking, completion history and maintenance-request application. This public repository contains **generic application code and blank deployment assets only**. It does not contain real machine records or employee/site history.

## Available functionality

- Equipment and PM-task register, due-status dashboard, completion history, and maintenance requests.
- QR machine pages, blank Excel import template, workbook import, and Excel report export.
- Flask application served with Waitress for Windows-friendly deployment.
- Generic x64 Windows Server installer and an automatic startup Scheduled Task.

## Windows Server deployment

Start with the [Windows Server installation guide](docs/WINDOWS_SERVER_INSTALL.md). Use the [latest successful main-branch Windows build artifact](https://github.com/danieloculus0-bot/PM-Tracker/actions/workflows/windows-server-release.yml), verify SHA256 values, and install **blank** before any separately approved data migration.

The installer uses `C:\ProgramData\PM Tracker` by default. The application keeps SQLite operational history (`pm_app.db`) separately from the machine/task workbook (`pm_data.xlsx`). Preserve both when updating or recovering an existing installation. GitHub Actions cannot access or migrate a private workstation's Flask/venv runtime or historical data.

## Developer smoke test (blank, synthetic workspace only)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Run those commands from a **fresh, disposable clone**, never the active site's working directory. The app uses its **process working directory** for `pm_app.db` and `pm_data.xlsx`, so do not run a test launch from any folder containing live data. The generic example binds `0.0.0.0:5000`; keep tests on trusted, isolated networks.

See [PM Tracker smoke CI](https://github.com/danieloculus0-bot/PM-Tracker/actions/workflows/smoke.yml) and [generic Windows build CI](https://github.com/danieloculus0-bot/PM-Tracker/actions/workflows/windows-server-release.yml) for current results. Build success is not proof of a successful site deployment.

## Data and safety boundaries

Do not commit or upload real assets, maintenance records, exports, site configuration, production information, or credentials to GitHub, including issues and Actions logs. Use only invented synthetic fixtures. `site_config.example.json` is a neutral template; customize the private `site_config.json` only on the target installation.

The application does not implement machine isolation, LOTO verification, user authentication, TLS termination, or production ERP integration. PM task notes are not substitutes for actual safety procedures.

See [AGENTS.md](AGENTS.md) for public-repository confidentiality rules.
