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
            wb.close()

    def test_import_machine_task_completion_and_request_then_repeat(self):
        wb = create_template()
        wb["Machines"].append(["GEN-M100", "Fictional Pump", "Demo", "Test"])
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
            "record_type": "task", "task_id": "GEN-T999", "task_machine_id": "UNKNOWN",
            "task_name": "Invalid", "frequency_unit": "Days", "frequency_value": "1"
        }).status_code, 400)


if __name__ == "__main__":
    unittest.main()
