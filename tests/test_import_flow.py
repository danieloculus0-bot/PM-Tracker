"""Synthetic-only regression tests for public generic import and manual-entry workflows."""
import importlib
import io
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook
from pm_import import create_template


class GenericImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_cwd = os.getcwd()
        cls._tmp = tempfile.TemporaryDirectory(prefix="pm-generic-import-")
        os.chdir(cls._tmp.name)
        cls.pm = importlib.import_module("app")
        cls.pm.init_db()
        cls.client = cls.pm.app.test_client()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._old_cwd)
        cls._tmp.cleanup()

    def test_blank_templates(self):
        for route, expected in (
            ("/template.xlsx", {"Machines", "PM_Tasks", "Completion_Log", "Maintenance_Requests"}),
            ("/machines-template.xlsx", {"Machines"}),
        ):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            wb = load_workbook(io.BytesIO(response.data))
            self.assertTrue(expected.issubset(set(wb.sheetnames)))
            self.assertEqual(wb["Machines"]["A1"].value, "Machine ID")
            if route == "/template.xlsx":
                guidance = " ".join(str(cell.value or "") for row in wb["READ_ME"] for cell in row)
                self.assertIn("Date-only entries retain the date", guidance)
                self.assertNotIn("importer uses noon", guidance)
            wb.close()

    def test_import_machine_task_completion_and_request_then_repeat(self):
        wb = create_template()
        wb["Machines"].append(["GEN-M100", "Fictional Pump", "Demo", "Test", "Synthetic Vendor"])
        wb["PM_Tasks"].append(["GEN-T100", "GEN-M100", "Fictional checklist", "Synthetic", "Days", 30])
        wb["Completion_Log"].append([
            "GEN-C100", "GEN-M100", "GEN-T100", "Synthetic User",
            datetime(2026, 10, 20), "07:35", "Delayed entry test", "Pass",
        ])
        wb["Maintenance_Requests"].append([
            "GEN-W100", "Synthetic Reporter", "2026-10-18T14:02:00",
            "GEN-M100", "Fictional Pump", "Test", "Low", "Closed",
            "Synthetic Assignee", "2026-10-20T15:00:00", "Synthetic issue", "Synthetic resolution",
        ])
        stream = io.BytesIO()
        wb.save(stream)
        wb.close()
        payload = stream.getvalue()

        for _ in range(2):
            response = self.client.post("/import", data={"file": (io.BytesIO(payload), "generic.xlsx")})
            self.assertEqual(response.status_code, 200, response.data.decode()[:800])
        conn = sqlite3.connect(self.pm.DB_FILE)
        completed = conn.execute(
            "SELECT completed_at, completion_notes FROM completions "
            "WHERE machine_id='GEN-M100' AND task_id='GEN-T100'"
        ).fetchall()
        requests = conn.execute(
            "SELECT request_number, description, status FROM maintenance_requests "
            "WHERE request_number='GEN-W100'"
        ).fetchall()
        self.assertEqual(completed, [("2026-10-20T07:35:00", "Delayed entry test")])
        self.assertEqual(requests, [("GEN-W100", "Synthetic issue", "Closed")])
        conn.close()

        # Updating only a machine name must not erase other populated fields.
        partial = create_template(machine_only=True)
        partial["Machines"].append(["GEN-M100", "Updated Fictional Pump"])
        stream2 = io.BytesIO()
        partial.save(stream2)
        partial.close()
        r = self.client.post("/import", data={
            "file": (io.BytesIO(stream2.getvalue()), "partial.xlsx")
        })
        self.assertEqual(r.status_code, 200, r.data.decode()[:500])
        wb_current = load_workbook(self.pm.EXCEL_FILE)
        rows = list(wb_current["Machines"].values)
        selected = next(x for x in rows[1:] if x[0] == "GEN-M100")
        self.assertEqual(selected[1], "Updated Fictional Pump")
        self.assertEqual(selected[4], "Synthetic Vendor")
        wb_current.close()

        # Date-only records retain the historical date without an invented time.
        no_time = create_template()
        no_time["Completion_Log"].append([
            "GEN-C101", "GEN-M100", "GEN-T100", "Another Synthetic User",
            datetime(2026, 10, 21), None, "Date only", "Pass",
        ])
        fileobj = io.BytesIO()
        no_time.save(fileobj)
        no_time.close()
        response = self.client.post("/import", data={
            "file": (io.BytesIO(fileobj.getvalue()), "date-only.xlsx")
        })
        self.assertEqual(response.status_code, 200, response.data.decode()[:500])
        conn = sqlite3.connect(self.pm.DB_FILE)
        stamp = conn.execute(
            "SELECT completed_at FROM completions WHERE operator_name=?",
            ("Another Synthetic User",)
        ).fetchone()[0]
        self.assertEqual(stamp, "2026-10-21")
        conn.close()

    def test_manual_entries(self):
        r = self.client.post("/manual-entry", data={
            "record_type": "machine", "machine_id": "GEN-M200",
            "machine_name": "Fictional Drill", "department": "Demo"
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.post("/manual-entry", data={
            "record_type": "machine", "machine_id": "GEN-M200",
            "machine_name": "Duplicate"
        }).status_code, 409)
        r = self.client.post("/manual-entry", data={
            "record_type": "task", "task_id": "GEN-T200", "task_machine_id": "GEN-M200",
            "task_name": "Synthetic check", "frequency_unit": "Weeks", "frequency_value": "2"
        })
        self.assertEqual(r.status_code, 200, r.data.decode()[:800])
        rows = [t for t in self.pm.read_tasks() if t["task_id"] == "GEN-T200"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["frequency_days"], 14)
        self.assertEqual(self.client.post("/manual-entry", data={
            "record_type": "task", "task_id": "GEN-T200", "task_machine_id": "GEN-M100",
            "task_name": "Duplicate across machines",
            "frequency_unit": "Weeks", "frequency_value": "2"
        }).status_code, 409)
        self.assertEqual(self.client.post("/manual-entry", data={
            "record_type": "task", "task_id": "GEN-T999", "task_machine_id": "UNKNOWN",
            "task_name": "Invalid", "frequency_unit": "Days", "frequency_value": "1"
        }).status_code, 400)


if __name__ == "__main__":
    unittest.main()
