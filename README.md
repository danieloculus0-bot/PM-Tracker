# PM Tracker

Generic preventive maintenance tracker for shops, facilities, makerspaces, and small manufacturing teams.

Features:
- Track machines and assets
- Track PM tasks by machine
- Add machines from the browser
- Add PM tasks from the browser
- Log PM completions from the browser
- Export Machines, PM_Tasks, and Completion_Log as CSV
- Seed data from pm_data.xlsx, CSV files, or data_seed.json

Data loading order on first run:
1. pm_data.xlsx in the project root
2. CSV files in a data folder named Machines.csv, PM_Tasks.csv, and Completion_Log.csv
3. data_seed.json
4. Blank tables

After first run, runtime edits are saved to pm_data.json.

Run locally:
1. Install dependencies from requirements.txt
2. Run app.py
3. Open http://127.0.0.1:5000

The included seed data comes from the uploaded workbook and was not expanded with fake machines or fake tasks.
