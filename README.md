# PM Tracker

Generic preventive maintenance tracker for shops, facilities, makerspaces, and small manufacturing teams.

This repository is evolving into the Forge manufacturing suite foundation. The current application is still the PM Tracker module, with early Forge support code for context routing and work order workmanship rules.

## Current PM Tracker features

- Track machines and assets
- Track PM tasks by machine
- Add machines from the browser
- Add PM tasks from the browser
- Log PM completions from the browser
- View completion history
- Export Machines, PM_Tasks, and Completion_Log as CSV
- Save host and port settings locally
- Start from header-only CSV templates without fake operational records

## Data behavior

Runtime edits are saved locally to:

- `pm_data.json`
- `pm_settings.json`

On first run, the app loads header/data rows from these CSV files if they exist:

- `data/Machines.csv`
- `data/PM_Tasks.csv`
- `data/Completion_Log.csv`

If the CSV files only contain headers, the app starts with blank tables. This is intentional. Do not commit fake customers, fake machines, fake tasks, fake jobs, fake people, fake records, or placeholder operational rows.

## Local files ignored by Git

These files are runtime/local-only and should not be committed:

- `pm_data.json`
- `pm_settings.json`
- `pm_app.db`
- `.venv/`
- `venv/`
- `__pycache__/`

## Forge foundation code

Early Forge support modules live under `forge/`:

- `forge/core/context_router.py` defines right-click/context routing rules between parts, jobs, work orders, machines, and quality records.
- `forge/work_order_builder/workmanship_rules.py` defines default work order note prompts based on the uploaded surface and edge integrity workmanship standard.

These modules are scaffolding for real manufacturing workflows, not sample-data demos.

## Run locally

1. Install dependencies from `requirements.txt`.
2. Run `python app.py`.
3. Open `http://127.0.0.1:5055` unless host/port settings have been changed.

## Test

Run:

```bash
pytest
```

## Design rules

- Keep it generic, not EZ Fab branded.
- Keep it tactical and useful.
- Do not add fake operational data.
- Prefer simple deployable workflows over placeholder screens.
- Preserve the professional ForgeVault-style direction: graphite/dark UI, orange accents, restrained controls.
