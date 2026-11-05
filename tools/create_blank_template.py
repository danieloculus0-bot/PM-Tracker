"""Generate generic empty Excel templates for releases and manual import."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pm_import import create_template

for name, only_machines in (
    ("PM_Tracker_Import_Template.xlsx", False),
    ("PM_Tracker_Machines_Only_Template.xlsx", True),
):
    target = ROOT / name
    wb = create_template(machine_only=only_machines)
    wb.save(target)
    wb.close()
    print(target)
