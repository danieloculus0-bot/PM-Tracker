# IT Review - PM Tracker Windows Server Deployment

## Purpose
PM Tracker is a lightweight internal preventive-maintenance web application intended for browser access across the company network.

## Runtime architecture
- Single Windows executable built with PyInstaller.
- Flask application served by Waitress.
- Default TCP port 5000.
- Server bind address `0.0.0.0`.
- Browser clients require no local installation.
- Runtime data is stored under `C:\ProgramData\PM Tracker`.

## Data stores
- `pm_data.xlsx`: machine master, PM task master, importable completion log.
- `pm_app.db`: SQLite runtime completion and maintenance-request records.
- `site_config.json`: site label, weather options, host, and port.

The repository and generic release contain no EZ or WMF production data.

## Startup
The deployment script registers a Windows Scheduled Task named **PM Tracker Server** running as SYSTEM at startup, with automatic restart attempts.

## Firewall
The deployment script creates an inbound TCP rule for the configured PM Tracker port on Domain and Private profiles only.

## Upgrades
Application upgrades replace the executable and deployment scripts while runtime data remains in the ProgramData directory. Uninstall removes the startup task and firewall rule but preserves runtime data.

## Migration
Users can migrate machine and PM data through **Import / Update Data**. A downloadable blank workbook is available from **Blank Template**.

## IT review items
- Assign a stable DNS name or server address.
- Confirm the preferred TCP port.
- Confirm backup coverage for `C:\ProgramData\PM Tracker`.
- Decide whether EZ and WMF use one shared instance or separate instances.
- Confirm whether Scheduled Task startup is acceptable or should be converted to the organization's preferred Windows service standard.
