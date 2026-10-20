# PM Tracker

Windows-friendly preventive maintenance tracker for manufacturing and facilities environments.

## Features

- Machine and asset tracking
- Preventive maintenance scheduling
- PM completion logging
- Bulk acknowledge / clear-all PM workflow
- Maintenance request and work-order tracking
- QR codes for machine pages
- Excel export
- Excel import / update workflow
- Downloadable blank import template
- Configurable site branding, weather, host, and port
- Waitress production WSGI server
- PyInstaller Windows executable build
- Windows Server installer pipeline

## Lockout/tagout (LOTO) guidance

PM Tracker uses the existing `PM_Tasks` **Safety Notes** column to identify task-specific hazards and reference approved site and machine-specific LOTO instructions. For tasks involving hazardous-energy exposure, populate Safety Notes with the applicable procedure identifier, isolation reference, and any task-specific precautions. Do not use a generic placeholder as a substitute for verified machine-specific instructions.

The machine task detail page displays a conditional-use LOTO reminder. It does not certify isolation, authorize an employee, or verify zero energy. Authorized personnel must perform the required isolation and verification before work begins. Site-specific LOTO documentation remains controlled outside this generic source repository.

## Runtime data

Site data is deliberately kept outside the source repository and outside the executable:

- `pm_data.xlsx` contains Machines, PM_Tasks, and Completion_Log sheets.
- `pm_app.db` contains runtime completion history and maintenance requests.
- `site_config.json` contains site-specific settings.

If `pm_data.xlsx` does not exist, PM Tracker creates a blank workbook automatically.

## Importing existing PM data

Open **Import / Update Data** in the application.

The importer accepts an `.xlsx` workbook containing any of these sheets:

- `Machines`
- `PM_Tasks`
- `Completion_Log`

Machines merge by `Machine ID`. PM tasks merge by `Task ID`. Existing machine/task rows are updated rather than blindly duplicated. Completion history is checked before insertion.

Use **Blank Template** in the application to download `PM_Tracker_Import_Template.xlsx` with the supported columns.

## Site configuration

Copy `site_config.example.json` to `site_config.json` and edit it for the deployment. For server access, use `0.0.0.0` as the host and have IT provide a stable DNS name or reserved/static address.

## Local run

```powershell
python -m pip install -r requirements.txt
python .\app.py
```

## Windows executable

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --name "PM Tracker" .\app.py
```

## Windows Server deployment

GitHub Actions builds a generic Windows Server deployment bundle and installer. The generic build contains no site-specific asset data or history.

The server installer is designed to deploy under `C:\ProgramData\PM Tracker`, preserve runtime data during upgrades, register PM Tracker to start automatically, and open the configured TCP port in Windows Firewall.

Site-specific data should be imported after deployment using the built-in spreadsheet importer, or copied into the deployment folder by authorized IT staff.

## Repository safety

Do not commit live machine data, PM history, runtime SQLite databases, site configuration, proprietary workbooks, deployment backups, or build output.


## EZ / company deployment profile

A sanitized deployment profile for IT review is provided under `deployments/company/`. It includes server architecture notes, spreadsheet migration instructions, and example EZ/company configuration files. No production machine data, PM history, internal addresses, or runtime databases are included.

## Repository audit note (2026-10-20)

**Status: independently useful preventive-maintenance application.** QR machine pages, scheduling, completion history, import/export, maintenance requests and server packaging are represented in source. Both October 15 PM smoke and EZ/company server-release workflows passed, but **workflow success does not prove an individual site has installed or safely configured a live server**. Generic LOTO notes cannot establish machine-specific isolation, employee authorization or verified zero energy. An Axiom source snapshot or intended PM integration must not be represented as a shared live database.

[Portfolio audit](https://github.com/danieloculus0-bot/Axiom_Beta/blob/main/docs/PORTFOLIO_AUDIT_2026-10-20.md).
