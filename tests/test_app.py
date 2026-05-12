import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app as pm_app


def setup_temp(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    (data_dir / 'Machines.csv').write_text(','.join(pm_app.MACHINES) + '\n', encoding='utf-8')
    (data_dir / 'PM_Tasks.csv').write_text(','.join(pm_app.TASKS) + '\n', encoding='utf-8')
    (data_dir / 'Completion_Log.csv').write_text(','.join(pm_app.LOGS) + '\n', encoding='utf-8')
    return pm_app.app.test_client()


def test_first_launch_has_no_fake_data(monkeypatch, tmp_path):
    client = setup_temp(monkeypatch, tmp_path)
    response = client.get('/')
    assert response.status_code == 200
    html = response.data.decode()
    assert '0</h2><p>Active machines</p>' in html
    assert '0</h2><p>Active PM tasks</p>' in html
    assert '0</h2><p>Completion records</p>' in html


def test_host_port_settings_save(monkeypatch, tmp_path):
    client = setup_temp(monkeypatch, tmp_path)
    response = client.post('/settings', data={'host': '127.0.0.1', 'port': '6060'})
    assert response.status_code == 200
    settings = pm_app.load_settings()
    assert settings['host'] == '127.0.0.1'
    assert settings['port'] == 6060


def test_add_machine_task_and_completion(monkeypatch, tmp_path):
    client = setup_temp(monkeypatch, tmp_path)
    machine = {field: '' for field in pm_app.MACHINES}
    machine.update({'Machine ID': 'M-1', 'Machine Name': 'Press', 'Active (Y/N)': 'Y'})
    assert client.post('/machines/new', data=machine).status_code == 302

    task = {field: '' for field in pm_app.TASKS}
    task.update({'Task ID': 'T-1', 'Machine ID': 'M-1', 'Task Name': 'Inspect', 'Frequency Unit (Days/Weeks/Months)': 'Days', 'Frequency Value': '7', 'Active (Y/N)': 'Y'})
    assert client.post('/tasks/new', data=task).status_code == 302

    complete = {'Completed By': 'Tester', 'Completion Date': '2026-05-12', 'Completion Time': '10:00', 'Pass/Fail': 'Pass', 'Notes': 'OK'}
    assert client.post('/complete/T-1', data=complete).status_code == 302

    data = pm_app.load()
    assert len(data['Machines']) == 1
    assert len(data['PM_Tasks']) == 1
    assert len(data['Completion_Log']) == 1


def test_csv_export(monkeypatch, tmp_path):
    client = setup_temp(monkeypatch, tmp_path)
    response = client.get('/export/Machines.csv')
    assert response.status_code == 200
    assert response.data.decode().startswith('Machine ID,Machine Name')
