import csv, io, json, os
from datetime import date, datetime, timedelta
from flask import Flask, Response, redirect, request, url_for

app = Flask(__name__)
DATA_FILE = 'pm_data.json'
SETTINGS_FILE = 'pm_settings.json'
CSV_DIR = 'data'

MACHINES = ['Machine ID','Machine Name','Department','Location','Manufacturer','Model','Serial Number','Asset Tag','Install Year','Criticality','Notes','Active (Y/N)']
TASKS = ['Task ID','Machine ID','Task Name','Task Description','Frequency Unit (Days/Weeks/Months)','Frequency Value','Responsible Role','Estimated Minutes','Safety Notes','Active (Y/N)']
LOGS = ['Completion ID','Machine ID','Task ID','Completed By','Completion Date','Completion Time','Notes','Pass/Fail']


def clean(v):
    return '' if v is None else str(v).strip()


def blank():
    return {'Machines': [], 'PM_Tasks': [], 'Completion_Log': []}


def default_settings():
    return {'host': '127.0.0.1', 'port': 5055}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding='utf-8') as f:
                settings = json.load(f)
            host = clean(settings.get('host')) or default_settings()['host']
            port = int(settings.get('port') or default_settings()['port'])
            if port < 1 or port > 65535:
                port = default_settings()['port']
            return {'host': host, 'port': port}
        except Exception:
            pass
    return default_settings()


def save_settings(host, port):
    settings = {'host': clean(host) or default_settings()['host'], 'port': int(port)}
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)
    return settings


def load_csv(name, fields):
    path = os.path.join(CSV_DIR, name + '.csv')
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return [{field: clean(row.get(field, '')) for field in fields} for row in csv.DictReader(f)]


def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    data = blank()
    data['Machines'] = load_csv('Machines', MACHINES)
    data['PM_Tasks'] = load_csv('PM_Tasks', TASKS)
    data['Completion_Log'] = load_csv('Completion_Log', LOGS)
    save(data)
    return data


def save(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def active(row):
    return clean(row.get('Active (Y/N)', 'Y')).upper() != 'N'


def find(rows, key, value):
    for row in rows:
        if clean(row.get(key)) == value:
            return row
    return None


def last_done(data, task_id):
    rows = [r for r in data['Completion_Log'] if clean(r.get('Task ID')) == task_id]
    return sorted(rows, key=lambda r: (clean(r.get('Completion Date')), clean(r.get('Completion Time'))), reverse=True)[0] if rows else None


def next_due(data, task):
    last = last_done(data, clean(task.get('Task ID')))
    if not last:
        return 'No completion logged'
    try:
        done = datetime.strptime(clean(last.get('Completion Date')), '%Y-%m-%d').date()
        value = int(float(clean(task.get('Frequency Value')) or 0))
    except Exception:
        return 'Unknown'
    unit = clean(task.get('Frequency Unit (Days/Weeks/Months)')).lower()
    if unit.startswith('week'):
        done += timedelta(weeks=value)
    elif unit.startswith('month'):
        done += timedelta(days=30 * value)
    else:
        done += timedelta(days=value)
    return done.isoformat()


def log_id(data):
    nums = []
    for row in data['Completion_Log']:
        raw = clean(row.get('Completion ID'))
        if raw.startswith('LOG-'):
            try:
                nums.append(int(raw.split('-', 1)[1]))
            except ValueError:
                pass
    return f'LOG-{(max(nums) if nums else 0) + 1:04d}'


def page(title, body):
    settings = load_settings()
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><style>
:root{{--bg:#080d12;--top:#0b1118;--side:#101821;--panel:#111a23;--panel2:#172330;--panel3:#1d2a37;--line:#2c3b4a;--line2:#405467;--text:#e6edf4;--muted:#9aa8b6;--muted2:#708294;--orange:#ff8a1c;--orange2:#d86b00;--bluebtn:#223142;--bluebtn2:#1a2633;--danger:#ff5d5d;}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif;font-size:14px}}a{{color:var(--text);text-decoration:none}}a:hover{{color:#fff}}.shell{{display:grid;grid-template-columns:285px 1fr;grid-template-rows:48px calc(100vh - 48px);min-height:100vh}}header{{grid-column:1/3;background:#080d12;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;padding:7px 12px}}.brand{{display:flex;align-items:center;font-size:25px;font-weight:800;letter-spacing:.01em;min-width:196px}}.brand:before{{content:"◆";color:var(--orange);font-size:24px;margin-right:10px;transform:rotate(45deg)}}.brand span{{color:var(--orange)}}.top-status{{flex:1;height:33px;border:1px solid var(--line2);background:#05090d;border-radius:4px;color:#b8c2cd;display:flex;align-items:center;padding:0 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.top-actions{{display:flex;gap:8px}}.side{{grid-row:2;background:var(--side);border-right:1px solid #1f2c38;overflow:auto}}.side-title{{height:39px;background:#15202b;color:#a7b2bf;text-transform:uppercase;font-size:12px;letter-spacing:.05em;display:flex;align-items:center;padding:0 14px}}nav{{padding:12px}}nav a{{display:flex;align-items:center;gap:10px;color:#aab5c2;border:1px solid transparent;border-radius:5px;padding:11px 12px;margin-bottom:7px}}nav a:hover{{background:#182534;border-color:#33485a;color:#eaf0f6}}nav a.primary{{background:var(--orange);color:#05090d;border-color:var(--orange);justify-content:center;font-weight:700}}.side-foot{{position:absolute;bottom:12px;left:12px;width:260px;color:var(--muted2);font-size:12px}}main{{grid-column:2;grid-row:2;display:grid;grid-template-columns:minmax(560px,1fr) 420px;gap:0;min-height:0}}.work{{padding:14px 20px 24px;overflow:auto}}.details{{background:#0b1118;border-left:1px solid #1f2c38;padding:18px 20px;overflow:auto}}h1{{font-size:25px;margin:8px 0 14px;font-weight:800}}h2{{font-size:21px;margin:0 0 12px}}p{{line-height:1.45}}.toolbar{{display:flex;gap:12px;margin:0 0 14px}}.searchbox{{height:33px;flex:1;border:1px solid var(--line2);background:#05090d;color:var(--muted);border-radius:4px;padding:0 12px}}.card{{background:transparent;border:0;padding:0;margin:0 0 18px;box-shadow:none}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(160px,1fr));gap:12px;margin-bottom:18px}}.grid .card{{background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:14px 16px}}.grid .card h2{{font-size:27px;margin:0 0 3px}}.grid .card p{{margin:0;color:var(--muted);text-transform:uppercase;font-size:12px;letter-spacing:.04em}}table{{width:100%;border-collapse:separate;border-spacing:0}}th{{background:#1b2a38;color:#aab7c5;font-size:12px;font-weight:500;text-align:left;padding:11px 10px}}td{{background:#101820;border-bottom:5px solid #080d12;color:#dce4ec;padding:12px 10px;vertical-align:top}}tr:hover td{{background:#1b2a38}}td a{{color:#f0f4f8}}.muted{{color:var(--muted)}}button,.btn{{border:1px solid var(--line2);background:linear-gradient(#243344,#1b2938);color:#e6edf4;border-radius:4px;padding:9px 16px;font-weight:600;cursor:pointer;display:inline-block}}button:hover,.btn:hover{{background:#2b3d50;color:#fff}}button[type=submit],.btn.primary{{background:var(--orange);border-color:var(--orange);color:#080d12}}button[type=submit]:hover,.btn.primary:hover{{background:#ff982f;color:#05090d}}.danger{{border-color:#b74141;color:#ffb3b3;background:#151014}}label{{display:block;color:#a9b5c1;font-size:12px;margin:8px 0 6px}}input,select,textarea{{width:100%;background:#070b10;border:1px solid var(--line2);border-radius:4px;color:#e6edf4;padding:9px 10px;outline:none}}input:focus,select:focus,textarea:focus{{border-color:var(--orange)}}textarea{{min-height:78px}}.right{{color:var(--muted);font-size:12px}}.meta{{border-top:1px solid #243341;margin-top:18px;padding-top:16px}}.meta-row{{display:grid;grid-template-columns:140px 1fr;gap:12px;margin:10px 0;color:#cdd6df}}.meta-row span:first-child{{color:var(--muted)}}.panel-preview{{height:190px;border:1px solid var(--line);background:#05090d;border-radius:5px;margin-bottom:20px;display:flex;align-items:center;justify-content:center;color:#536273}}.panel-preview:before{{content:"PM";border:2px solid var(--orange);border-radius:50%;width:62px;height:62px;display:flex;align-items:center;justify-content:center;color:var(--orange);font-weight:800}}
@media(max-width:1050px){{.shell{{display:block}}header{{position:sticky;top:0;z-index:2}}.side{{border-right:0}}.side-foot{{position:static;width:auto;margin:20px 12px}}main{{display:block}}.details{{border-left:0;border-top:1px solid #1f2c38}}.grid{{grid-template-columns:1fr}}.top-status{{display:none}}}}
</style></head><body><div class="shell"><header><div class="brand">PM<span>Tracker</span></div><div class="top-status">Host {settings['host']}  |  Port {settings['port']}  |  Preventive maintenance command center</div><div class="top-actions"><a class="btn" href="/settings">Health</a><a class="btn" href="/export/Machines.csv">Export</a><a class="btn primary" href="/machines/new">Add Machine</a></div></header><aside class="side"><div class="side-title">Modules</div><nav><a class="primary" href="/">Dashboard</a><a href="/machines/new">Add Machine</a><a href="/tasks/new">Add PM Task</a><a href="/completions">Completion Log</a><a href="/settings">Host / Port</a></nav><div class="side-foot">Ready. Generic PM tracker shell with local runtime data and header-only import templates.</div></aside><main><section class="work">{body}</section><aside class="details"><div class="panel-preview"></div><h2>PM Tracker</h2><p class="muted">Machine records, task schedules, completion history, exports, and local host settings.</p><div class="meta"><div class="meta-row"><span>Runtime data</span><div>pm_data.json</div></div><div class="meta-row"><span>Settings</span><div>pm_settings.json</div></div><div class="meta-row"><span>CSV source</span><div>data folder templates</div></div><div class="meta-row"><span>Status</span><div>Local first</div></div></div></aside></main></div></body></html>'''


@app.route('/')
def home():
    data = load()
    machines = [m for m in data['Machines'] if active(m)]
    tasks = [t for t in data['PM_Tasks'] if active(t)]
    rows = ''.join(f"<tr><td><a href='/machine/{m['Machine ID']}'>{m['Machine Name']}</a></td><td>{m['Machine ID']}</td><td>{m['Department']}</td><td>{m['Location']}</td><td>{m['Criticality']}</td></tr>" for m in machines)
    return page('PM Tracker', f"<div class='toolbar'><input class='searchbox' placeholder='Search machine, task, department, location, metadata...'><a class='btn' href='/'>Refresh</a><a class='btn primary' href='/tasks/new'>Add Task</a></div><h1>Preventive Maintenance Tracker</h1><div class='grid'><div class='card'><h2>{len(machines)}</h2><p>Active machines</p></div><div class='card'><h2>{len(tasks)}</h2><p>Active PM tasks</p></div><div class='card'><h2>{len(data['Completion_Log'])}</h2><p>Completion records</p></div></div><div class='card'><h2>Machines</h2><table><tr><th>Machine</th><th>ID</th><th>Department</th><th>Location</th><th>Criticality</th></tr>{rows}</table></div>")


@app.route('/settings', methods=['GET','POST'])
def settings():
    current = load_settings()
    msg = ''
    if request.method == 'POST':
        try:
            new = save_settings(request.form.get('host'), request.form.get('port'))
            msg = f"<p class='muted'>Saved. Restart the app for server binding changes to take effect. New setting: {new['host']} port {new['port']}.</p>"
            current = new
        except Exception as exc:
            msg = f"<p class='muted'>Could not save settings: {exc}</p>"
    body = f"<h1>Host and Port</h1><div class='card'><form method='post'><div class='grid'><label>Host<input name='host' value='{current['host']}'></label><label>Port<input name='port' type='number' min='1' max='65535' value='{current['port']}'></label></div><button>Save Host/Port</button></form>{msg}<p class='muted'>Use 127.0.0.1 for local-only access. Use 0.0.0.0 only when you intentionally want LAN access.</p></div>"
    return page('Host and Port', body)


@app.route('/machine/<machine_id>')
def machine(machine_id):
    data = load()
    machine_row = find(data['Machines'], 'Machine ID', machine_id)
    if not machine_row:
        return page('Not found', '<div class="card">Machine not found.</div>')
    rows = ''
    for task in [t for t in data['PM_Tasks'] if clean(t.get('Machine ID')) == machine_id and active(t)]:
        rows += f"<tr><td>{task['Task Name']}<br><span class='muted'>{task['Task ID']}</span></td><td>{task['Task Description']}</td><td>Every {task['Frequency Value']} {task['Frequency Unit (Days/Weeks/Months)']}</td><td>{task['Responsible Role']}</td><td>{next_due(data, task)}</td><td><a href='/complete/{task['Task ID']}'>Log completion</a></td></tr>"
    body = f"<h1>{machine_row['Machine Name']}</h1><div class='card'><p><b>ID:</b> {machine_row['Machine ID']} | <b>Department:</b> {machine_row['Department']} | <b>Location:</b> {machine_row['Location']} | <b>Criticality:</b> {machine_row['Criticality']}</p><p><b>Manufacturer:</b> {machine_row['Manufacturer']} | <b>Model:</b> {machine_row['Model']} | <b>Serial:</b> {machine_row['Serial Number']} | <b>Asset:</b> {machine_row['Asset Tag']}</p><p>{machine_row['Notes']}</p></div><div class='card'><h2>PM Tasks</h2><table><tr><th>Task</th><th>Description</th><th>Frequency</th><th>Role</th><th>Next Due</th><th></th></tr>{rows}</table></div><p><a class='btn primary' href='/tasks/new?machine_id={machine_id}'>Add Task</a></p>"
    return page(machine_row['Machine Name'], body)


@app.route('/machines/new', methods=['GET','POST'])
def add_machine():
    data = load()
    if request.method == 'POST':
        row = {field: clean(request.form.get(field, '')) for field in MACHINES}
        row['Active (Y/N)'] = row['Active (Y/N)'] or 'Y'
        if row['Machine ID'] and row['Machine Name']:
            data['Machines'].append(row)
            save(data)
            return redirect(url_for('machine', machine_id=row['Machine ID']))
    fields = ''.join(f"<label>{field}<input name='{field}' value='Y'></label>" if field == 'Active (Y/N)' else f"<label>{field}<input name='{field}'></label>" for field in MACHINES)
    return page('Add Machine', f"<h1>Add Machine</h1><div class='card'><form method='post'><div class='grid'>{fields}</div><button>Save Machine</button></form></div>")


@app.route('/tasks/new', methods=['GET','POST'])
def add_task():
    data = load()
    selected = clean(request.args.get('machine_id'))
    if request.method == 'POST':
        row = {field: clean(request.form.get(field, '')) for field in TASKS}
        row['Active (Y/N)'] = row['Active (Y/N)'] or 'Y'
        if row['Task ID'] and row['Machine ID'] and row['Task Name']:
            data['PM_Tasks'].append(row)
            save(data)
            return redirect(url_for('machine', machine_id=row['Machine ID']))
    options = ''.join(f"<option value='{m['Machine ID']}' {'selected' if m['Machine ID'] == selected else ''}>{m['Machine ID']} - {m['Machine Name']}</option>" for m in data['Machines'] if active(m))
    body = f"<h1>Add PM Task</h1><div class='card'><form method='post'><div class='grid'><label>Task ID<input name='Task ID'></label><label>Machine<select name='Machine ID'>{options}</select></label><label>Task Name<input name='Task Name'></label><label>Frequency Unit<select name='Frequency Unit (Days/Weeks/Months)'><option>Days</option><option>Weeks</option><option>Months</option></select></label><label>Frequency Value<input name='Frequency Value' type='number' value='1'></label><label>Responsible Role<input name='Responsible Role'></label><label>Estimated Minutes<input name='Estimated Minutes' type='number'></label><label>Active (Y/N)<input name='Active (Y/N)' value='Y'></label></div><label>Task Description<textarea name='Task Description'></textarea></label><label>Safety Notes<textarea name='Safety Notes'></textarea></label><button>Save Task</button></form></div>"
    return page('Add Task', body)


@app.route('/complete/<task_id>', methods=['GET','POST'])
def complete(task_id):
    data = load()
    task = find(data['PM_Tasks'], 'Task ID', task_id)
    if not task:
        return page('Not found', '<div class="card">Task not found.</div>')
    if request.method == 'POST':
        now = datetime.now()
        row = {'Completion ID': log_id(data), 'Machine ID': task['Machine ID'], 'Task ID': task['Task ID'], 'Completed By': clean(request.form.get('Completed By')), 'Completion Date': clean(request.form.get('Completion Date')) or now.date().isoformat(), 'Completion Time': clean(request.form.get('Completion Time')) or now.strftime('%H:%M'), 'Notes': clean(request.form.get('Notes')), 'Pass/Fail': clean(request.form.get('Pass/Fail')) or 'Pass'}
        data['Completion_Log'].append(row)
        save(data)
        return redirect(url_for('machine', machine_id=task['Machine ID']))
    body = f"<h1>Log Completion</h1><div class='card'><p>{task['Task Name']} | {task['Task ID']}</p><form method='post'><div class='grid'><label>Completed By<input name='Completed By' required></label><label>Date<input type='date' name='Completion Date' value='{date.today().isoformat()}'></label><label>Time<input type='time' name='Completion Time' value='{datetime.now().strftime('%H:%M')}'></label><label>Pass/Fail<select name='Pass/Fail'><option>Pass</option><option>Fail</option></select></label></div><label>Notes<textarea name='Notes'></textarea></label><button>Save Completion</button></form></div>"
    return page('Log Completion', body)


@app.route('/completions')
def completions():
    data = load()
    rows = ''.join(f"<tr><td>{r['Completion ID']}</td><td>{r['Completion Date']}</td><td>{r['Completion Time']}</td><td>{r['Machine ID']}</td><td>{r['Task ID']}</td><td>{r['Completed By']}</td><td>{r['Pass/Fail']}</td><td>{r['Notes']}</td></tr>" for r in reversed(data['Completion_Log']))
    return page('Completions', f"<h1>Completion Log</h1><div class='card'><table><tr><th>ID</th><th>Date</th><th>Time</th><th>Machine</th><th>Task</th><th>By</th><th>Result</th><th>Notes</th></tr>{rows}</table></div>")


@app.route('/export/<table>.csv')
def export_csv(table):
    fields = {'Machines': MACHINES, 'PM_Tasks': TASKS, 'Completion_Log': LOGS}.get(table)
    if not fields:
        return Response('Unknown table', status=404)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(load()[table])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={table}.csv'})


if __name__ == '__main__':
    settings = load_settings()
    print(f"PM Tracker starting on host {settings['host']} port {settings['port']}")
    app.run(debug=True, host=settings['host'], port=settings['port'])
