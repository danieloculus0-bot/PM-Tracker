# Spreadsheet Migration Guide

PM Tracker is designed so existing PM programs can be moved to a new server without hard-coding site data into the application.

## Built-in browser import

1. Open PM Tracker.
2. Select **Import / Update Data**.
3. Choose an `.xlsx` workbook.
4. Submit the import.
5. Review the counts reported by the application.

Before changing `pm_data.xlsx`, PM Tracker creates a timestamped backup of the current workbook.

## Workbook sheets

### Machines
Required:
- Machine ID
- Machine Name

Rows merge by **Machine ID**.

### PM_Tasks
Required:
- Machine ID

Strongly recommended:
- Task ID
- Task Name
- Task Description
- Frequency Value
- Frequency Unit (Days/Weeks/Months)

Rows merge by **Task ID**.

### Completion_Log
Recommended:
- Machine ID
- Task ID
- Completed By
- Completion Date
- Notes

Completion imports are deduplicated using machine, task, completion date, and completed-by name.

## Blank template
Select **Blank Template** in PM Tracker to download the supported workbook structure.

## Repository policy
Do not commit completed migration workbooks, production machine lists, PM history, SQLite databases, or production `site_config.json` files to GitHub.
