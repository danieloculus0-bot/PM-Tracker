# Excel import and manual-entry guide

PM Tracker supports two complementary workflows: **import a generic Excel machine register**, or **enter a machine and its PM tasks manually** in the browser. A partial import is valid: start with Machines and add PM_Tasks later.

## Generic templates

- Download the machines-only template from a running tracker via the **Machines Template** navigation link (`/machines-template.xlsx`).
- Download the full template from a running tracker via **Full Excel Template** (`/template.xlsx`).
- For an offline template, run `python tools/create_blank_template.py` in a disposable development checkout, or retrieve the **generic Windows Server release artifact** from Actions. CI creates both empty `PM_Tracker_Machines_Only_Template.xlsx` and `PM_Tracker_Import_Template.xlsx`. No real rows are included.

These sheets can be imported separately; names and first-row headers must match:

| Sheet | Minimum fields | Behavior |
| --- | --- | --- |
| `Machines` | Machine ID, Machine Name | Adds or updates machine rows by Machine ID |
| `PM_Tasks` | Task ID, Machine ID, Task Name | Adds or updates task rows by Task ID |
| `Completion_Log` | Machine ID, Task ID, Completed By, Completion Date | Adds historical completions to SQLite and the workbook; optional Completion Time and Notes |
| `Maintenance_Requests` | Request Number, Submitted By, Submitted At, Description | Inserts historical requests if Request Number does not already exist |

Other fields are optional. For completion dates, use `YYYY-MM-DD`. Optional time uses `HH:MM` (24-hour) or `HH:MM:SS`. Without time, the importer uses **12:00** on the entered historical date, not today's timestamp. Keep original evidence and explain delayed entries in Notes as needed.

### Load order

1. On an authorized **private** deployment, back up both `pm_app.db` and `pm_data.xlsx` before any imports.
2. Download the blank machines-only workbook, fill real equipment values **locally**, and upload it to `/import`. Do not commit filled sheets to GitHub.
3. Add tasks using the `/manual-entry` browser page or use the full workbook's `PM_Tasks` sheet.
4. If applicable, add historical completion dates to `Completion_Log`, and maintenance requests to `Maintenance_Requests`. Re-importing the same request number or exact completion/person pairing will not create duplicate SQLite records.
5. Review machine/task totals, completion dates and request details. Keep a separate backup of the pre-import state.

### Manual browser entry

Choose **Manual Entry**. Add a machine (unique Machine ID), then add a PM task (unique combination of Machine ID and Task ID, task name, frequency and role). These write to `pm_data.xlsx`. The normal work-completion and maintenance-request pages continue to handle operations and records.

## Migration versus spreadsheet import

A full migration from an existing installation is **not the same as importing a spreadsheet**. Historical `pm_app.db` contains exact completion timestamps, operator names, notes and maintenance-request state, while `pm_data.xlsx` contains machine/task definitions and potentially an additional Completion_Log sheet. Preserve and transfer **both** using an access-controlled private channel. On Windows, install the generic application, stop its `PM Tracker Server` Scheduled Task, back up its initial blank data, restore verified source copies of both stores, and restart. Compare counts and dates before allowing users in. See [Windows server guide](WINDOWS_SERVER_INSTALL.md).

Neither generic template nor public CI contains historical employer/customer data.

## Limitations

- Excel import writes a workbook and SQLite as separate stores. It is **not** an all-or-nothing transaction; take a full backup before importing.
- An import is not live database synchronization. Multiple people importing or editing a workbook at once may overwrite changes. Coordinate with the server administrator.
- The app currently lacks built-in user authentication. Site IT must restrict access using suitable internal-network controls.
- Full original history may include records not representable by the limited Excel import fields; retain `pm_app.db` as the authoritative original.
