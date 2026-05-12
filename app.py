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
:root{{--bg:#070b10;--bg2:#0b1118;--panel:#121923;--panel2:#151f2b;--panel3:#1b2633;--line:#2b3a4a;--line2:#3b5166;--text:#e8edf3;--muted:#8fa1b5;--accent:#38bdf8;--accent2:#0ea5e9;--accent3:#7dd3fc;--warn:#f59e0b;--good:#22c55e;--bad:#ef4444;--shadow:0 18px 45px rgba(0,0,0,.38);}}
*{{box-sizing:border-box}}body{{font-family:Arial,Helvetica,sans-serif;background:radial-gradient(circle at 18% -8%,rgba(56,189,248,.16),transparent 34%),radial-gradient(circle at 88% 0,rgba(14,165,233,.09),transparent 28%),linear-gradient(180deg,var(--bg),#0a0f15 45%,#070b10);color:var(--text);margin:0;min-height:100vh}}body:before{{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.35),transparent 72%)}}
header{{position:sticky;top:0;z-index:10;background:linear-gradient(180deg,#0b1118,#06090d);padding:14px 24px 16px;border-bottom:1px solid var(--line);box-shadow:0 12px 28px rgba(0,0,0,.42)}}header:before{{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg,transparent,var(--accent),var(--accent2),transparent)}}main{{max-width:1240px;margin:auto;padding:26px 24px 40px;position:relative}}
a{{color:var(--accent3);text-decoration:none}}a:hover{{color:#fff;text-decoration:none}}header b a{{letter-spacing:.08em;text-transform:uppercase;color:#f8fbff;font-size:16px}}header b a:before{{content:"▰";color:var(--accent);margin-right:9px;text-shadow:0 0 18px rgba(56,189,248,.75)}}nav{{margin-top:12px;display:flex;gap:10px;flex-wrap:wrap}}nav a{{margin:0;color:#cfe8f6;background:linear-gradient(180deg,#172232,#111923);border:1px solid var(--line);border-radius:999px;padding:7px 12px;font-size:13px;font-weight:700;box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}}nav a:hover{{border-color:var(--accent);background:linear-gradient(180deg,#1d3042,#142131);box-shadow:0 0 0 1px rgba(56,189,248,.18),0 0 22px rgba(56,189,248,.10)}}
h1{{margin:0 0 18px;font-size:30px;letter-spacing:.01em}}h2{{margin-top:0;color:#f5f9ff}}p{{line-height:1.5}}.card{{background:linear-gradient(180deg,rgba(27,38,51,.96),rgba(15,22,31,.98));border:1px solid var(--line);border-radius:14px;padding:18px;margin:0 0 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}}.card:before{{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(125,211,252,.65),transparent)}}.card h2+table{{margin-top:6px}}
table{{width:100%;border-collapse:separate;border-spacing:0;background:rgba(6,10,15,.35);border:1px solid var(--line);border-radius:12px;overflow:hidden}}td,th{{border-bottom:1px solid var(--line);padding:10px 11px;text-align:left;vertical-align:top}}th{{color:#d8edff;background:linear-gradient(180deg,#182536,#101822);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}td{{color:#dbe5ee}}tr:last-child td{{border-bottom:0}}tr:hover td{{background:rgba(56,189,248,.045)}}.muted{{color:var(--muted)}}
input,select,textarea{{width:100%;padding:10px 11px;border-radius:9px;border:1px solid var(--line);background:#070b10;color:var(--text);outline:none;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}}input:focus,select:focus,textarea:focus{{border-color:var(--accent);box-shadow:0 0 0 3px rgba(56,189,248,.13)}}textarea{{min-height:76px}}label{{display:block;margin:8px 0;color:var(--muted);font-size:13px;font-weight:700}}button,.btn{{display:inline-block;background:linear-gradient(180deg,var(--accent),var(--accent2));color:#00111f;border:0;border-radius:10px;padding:10px 15px;font-weight:800;text-decoration:none;box-shadow:0 10px 22px rgba(14,165,233,.22);cursor:pointer}}button:hover,.btn:hover{{color:#00111f;filter:brightness(1.08)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.right{{float:right;color:var(--muted);font-size:12px;background:#08101a;border:1px solid var(--line);border-radius:999px;padding:6px 10px}}.card h2{{font-size:28px;color:#ffffff;margin-bottom:2px}}.card h2+p{{margin-top:0;color:var(--muted);text-transform:uppercase;font-size:12px;letter-spacing:.08em;font-weight:800}}
@media(max-width:720px){{header{{padding:13px 16px}}main{{padding:20px 14px}}.right{{float:none;display:inline-block;margin:10px 0 0}}table{{font-size:13px}}}}
</style></head><body><header><b><a href="/">PM Tracker</a></b><span class="right">Host {settings['host']} | Port {settings['port']}</span><nav><a href="/machines/new">Add Machine</a><a href="/tasks/new">Add Task</a><a href="/completions">Completions</a><a href="/settings">Host/Port</a></nav></header><main>{body}</main></body></html>'''


@app.route('/')
def home():
    data = load()
    machines = [m for m in data['Machines'] if active(m)]
    tasks = [t for t in data['PM_Tasks'] if active(t)]
    rows = ''.join(f"<tr><td><a href='/machine/{m['Machine ID']}'>{m['Machine Name']}</a></td><td>{m['Machine ID']}</td><td>{m['Department']}</td><td>{m['Location']}</td><td>{m['Criticality']}</td></tr>" for m in machines)
    return page('PM Tracker', f"<h1>Preventive Maintenance Tracker</h1><div class='grid'><div class='card'><h2>{len(machines)}</h2><p>Active machines</p></div><div class='card'><h2>{len(tasks)}</h2><p>Active PM tasks</p></div><div class='card'><h2>{len(data['Completion_Log'])}</h2><p>Completion records</p></div></div><div class='card'><h2>Machines</h2><table><tr><th>Machine</th><th>ID</th><th>Department</th><th>Location</th><th>Criticality</th></tr>{rows}</table></div>")


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
    body = f"<h1>{machine_row['Machine Name']}</h1><div class='card'><p><b>ID:</b> {machine_row['Machine ID']} | <b>Department:</b> {machine_row['Department']} | <b>Location:</b> {machine_row['Location']} | <b>Criticality:</b> {machine_row['Criticality']}</p><p><b>Manufacturer:</b> {machine_row['Manufacturer']} | <b>Model:</b> {machine_row['Model']} | <b>Serial:</b> {machine_row['Serial Number']} | <b>Asset:</b> {machine_row['Asset Tag']}</p><p>{machine_row['Notes']}</p></div><div class='card'><h2>PM Tasks</h2><table><tr><th>Task</th><th>Description</th><th>Frequency</th><th>Role</th><th>Next Due</th><th></th></tr>{rows}</table></div><p><a class='btn' href='/tasks/new?machine_id={machine_id}'>Add Task</a></p>"
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
