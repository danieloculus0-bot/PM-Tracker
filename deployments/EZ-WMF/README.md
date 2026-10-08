# EZ / WMF Server Deployment Profile

This deployment profile is intentionally sanitized. It contains no machine list, serial numbers, PM history, maintenance history, internal IP addresses, credentials, or other site-specific operating data.

The same PM Tracker executable can be deployed for EZ Fabricating, WMF, or as a shared instance. Site-specific information remains external to the executable.

## Recommended server layout

`C:\ProgramData\PM Tracker\`

Runtime files:
- `PM Tracker.exe`
- `site_config.json`
- `pm_data.xlsx`
- `pm_app.db`

The installer registers PM Tracker to start at Windows startup and creates a Domain/Private Windows Firewall rule for the configured TCP port.

## First deployment

1. Install the Windows Server package as Administrator.
2. Copy the desired example configuration to `site_config.json` and adjust the site name, port, and optional weather settings.
3. Start or restart the **PM Tracker Server** scheduled task.
4. Open the application in a browser using the server DNS name and configured port.
5. Use **Import / Update Data** to migrate existing machines, PM tasks, and completion history from Excel.
6. Use **Blank Template** if a clean import workbook is needed.

## Deployment choices

### Separate EZ and WMF instances
Deploy the same executable with separate data directories and different ports or server names.

### Shared EZ / WMF instance
Deploy one instance and import both sites' machine and PM data into the same workbook. Use Department and Location to distinguish sites.

No EZ or WMF production data is stored in this repository.
