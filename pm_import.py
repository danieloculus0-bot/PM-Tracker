"""Generic, public-safe Excel import and template helpers for PM Tracker."""
from datetime import date, datetime, time, timedelta
from io import BytesIO

from openpyxl import Workbook


MACHINE_HEADERS = [
    "Machine ID", "Machine Name", "Department", "Location", "Manufacturer",
    "Model", "Serial Number", "Asset Tag", "Install Year", "Criticality",
    "Notes", "Active (Y/N)",
]
TASK_HEADERS = [
    "Task ID", "Machine ID", "Task Name", "Task Description",
    "Frequency Unit (Days/Weeks/Months)", "Frequency Value",
    "Responsible Role", "Estimated Minutes", "Safety Notes", "Active (Y/N)",
]
COMPLETION_HEADERS = [
    "Completion ID", "Machine ID", "Task ID", "Completed By", "Completion Date",
    "Completion Time", "Notes", "Pass/Fail",
]
REQUEST_HEADERS = [
    "Request Number", "Submitted By", "Submitted At", "Machine ID",
    "Machine Name", "Location", "Priority", "Status", "Assigned To",
    "Closed At", "Description", "Resolution Notes",
]


def create_template(machine_only=False):
    """Workbook compatible with the /import page; no site data."""
    wb = Workbook()
    wb.remove(wb.active)
    sheets = [("Machines", MACHINE_HEADERS)]
    if not machine_only:
        sheets.extend((
            ("PM_Tasks", TASK_HEADERS),
            ("Completion_Log", COMPLETION_HEADERS),
            ("Maintenance_Requests", REQUEST_HEADERS),
        ))
    for name, headers in sheets:
        sheet = wb.create_sheet(name)
        sheet.append(headers)
        sheet.freeze_panes = "A2"
        for cell in sheet[1]:
            cell.font = __import__("openpyxl").styles.Font(bold=True, color="FFFFFF")
            cell.fill = __import__("openpyxl").styles.PatternFill("solid", fgColor="142233")
        for i, header in enumerate(headers, 1):
            sheet.column_dimensions[__import__("openpyxl").utils.get_column_letter(i)].width = min(38, max(16, len(header) + 4))
    guide = wb.create_sheet("READ_ME")
    for pair in [
        ("PM Tracker", "Generic template. Do not upload actual business records to public GitHub."),
        ("Machines", "Machine ID and Machine Name required."),
        ("PM_Tasks", "Task ID, Machine ID and Task Name required. First load machines, then add tasks in Excel or the manual-entry page."),
        ("Completion_Log", "Actual completion date, time if known, machine, task and completed-by name. If no time is known, importer uses noon."),
        ("Maintenance_Requests", "Optional. Use Request Number and historical Submitted At timestamps for original work orders."),
        ("Partial imports", "Unused sheets may remain empty. Machines-only template is available separately."),
        ("History migration", "Keep a private pm_app.db backup too; the Excel template is not a complete replacement for SQLite historical records."),
    ]:
        guide.append(pair)
    guide.column_dimensions["A"].width = 24
    guide.column_dimensions["B"].width = 110
    return wb


def completed_at_from_excel(row):
    """Return historical ISO timestamp. A missing clock time defaults to noon."""
    raw_date = row.get("Completion Date")
    if isinstance(raw_date, datetime):
        dt = raw_date
    elif isinstance(raw_date, date):
        dt = datetime.combine(raw_date, time.min)
    elif raw_date is not None and str(raw_date).strip():
        value = str(raw_date).strip()
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            dt = None
            for pattern in ("%m/%d/%Y", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(value, pattern)
                    break
                except ValueError:
                    pass
        if dt is None:
            raise ValueError("Invalid Completion Date: use YYYY-MM-DD")
    else:
        raise ValueError("Completion Date is required")

    raw_time = row.get("Completion Time")
    if raw_time is None or str(raw_time).strip() == "":
        # Preserve time already present in full date+time; otherwise noon.
        if dt.time() == time.min:
            dt = dt.replace(hour=12)
    elif isinstance(raw_time, datetime):
        dt = datetime.combine(dt.date(), raw_time.time())
    elif isinstance(raw_time, time):
        dt = datetime.combine(dt.date(), raw_time)
    elif isinstance(raw_time, (int, float)) and 0 <= raw_time < 1:
        dt = datetime.combine(dt.date(), time.min) + timedelta(seconds=round(raw_time * 86400))
    else:
        parsed = None
        for pattern in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
            try:
                parsed = datetime.strptime(str(raw_time).strip(), pattern).time()
                break
            except ValueError:
                pass
        if parsed is None:
            raise ValueError("Invalid Completion Time: use HH:MM or HH:MM:SS")
        dt = datetime.combine(dt.date(), parsed)
    return dt.isoformat(timespec="seconds")


def import_requests(conn, rows):
    """Insert historical request rows only if each request number is new."""
    existing = {str(r[0]).strip() for r in conn.execute(
        "SELECT request_number FROM maintenance_requests WHERE request_number IS NOT NULL"
    ).fetchall()}
    imported = 0
    for row in rows:
        request_number = str(row.get("Request Number") or "").strip()
        submitted_by = str(row.get("Submitted By") or "").strip()
        description = str(row.get("Description") or "").strip()
        submitted_at = row.get("Submitted At")
        if not request_number and not any(str(v or "").strip() for v in row.values()):
            continue
        if not request_number or not submitted_by or not description or not submitted_at:
            raise ValueError("Maintenance_Requests row requires Request Number, Submitted By, Submitted At, Description")
        if request_number in existing:
            continue
        if isinstance(submitted_at, (datetime, date)):
            submitted_at = (
                submitted_at.isoformat(timespec="seconds")
                if isinstance(submitted_at, datetime)
                else datetime.combine(submitted_at, time(12)).isoformat(timespec="seconds")
            )
        else:
            submitted_at = str(submitted_at).strip()
            datetime.fromisoformat(submitted_at)
        closed_at = row.get("Closed At")
        if isinstance(closed_at, datetime):
            closed_at = closed_at.isoformat(timespec="seconds")
        elif isinstance(closed_at, date):
            closed_at = datetime.combine(closed_at, time(12)).isoformat(timespec="seconds")
        elif closed_at:
            closed_at = str(closed_at).strip()
            datetime.fromisoformat(closed_at)
        else:
            closed_at = None
        conn.execute("""
            INSERT INTO maintenance_requests (
                request_number, submitted_by, submitted_at,
                machine_id, machine_name, location, priority,
                description, status, assigned_to, resolution_notes, closed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_number, submitted_by, submitted_at,
            str(row.get("Machine ID") or "").strip(),
            str(row.get("Machine Name") or "").strip(),
            str(row.get("Location") or "").strip(),
            str(row.get("Priority") or "Medium").strip(),
            description, str(row.get("Status") or "Open").strip(),
            str(row.get("Assigned To") or "").strip(),
            str(row.get("Resolution Notes") or "").strip(),
            closed_at,
        ))
        existing.add(request_number)
        imported += 1
    return imported
