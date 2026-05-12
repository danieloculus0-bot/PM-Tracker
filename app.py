import csv
import html
import io
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from flask import Flask, Response, redirect, request, url_for

app = Flask(__name__)

DATA_FILE = 'pm_data.json'
DB_FILE = 'pm_app.db'
SETTINGS_FILE = 'pm_settings.json'
CSV_DIR = 'data'

MACHINES = ['Machine ID','Machine Name','Department','Location','Manufacturer','Model','Serial Number','Asset Tag','Install Year','Criticality','Notes','Active (Y/N)']
TASKS = ['Task ID','Machine ID','Task Name','Task Description','Frequency Unit (Days/Weeks/Months)','Frequency Value','Responsible Role','Estimated Minutes','Safety Notes','Active (Y/N)']
LOGS = ['Completion ID','Machine ID','Task ID','Completed By','Completion Date','Completion Time','Notes','Pass/Fail']

TABLES = {
    'Machines': {'sqlite': 'machines', 'fields': MACHINES, 'key': 'Machine ID'},
    'PM_Tasks': {'sqlite': 'pm_tasks', 'fields': TASKS, 'key': 'Task ID'},
    'Completion_Log': {'sqlite': 'completion_log', 'fields': LOGS, 'key': 'Completion ID'},
}


def clean(v):
    return '' if v is None else str(v).strip()


def h(v):
    return html.escape(clean(v), quote=True)


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


def quote_ident(name):
    return '"' + name.replace('"', '""') + '"'


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn):
    for meta in TABLES.values():
        fields = meta['fields']
        key = meta['key']
        columns = []
        for field in fields:
            definition = f'{quote_ident(field)} TEXT NOT NULL DEFAULT ""'
            if field == key:
                definition += ' PRIMARY KEY'
            columns.append(definition)
        conn.execute(f'CREATE TABLE IF NOT EXISTS {quote_ident(meta["sqlite"])} ({", ".join(columns)})')
    conn.commit()


def load_csv(name, fields):
    path = os.path.join(CSV_DIR, name + '.csv')
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return [{field: clean(row.get(field, '')) for field in fields} for row in csv.DictReader(f)]


def load_json_seed():
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            raw = json.load(f)
        data = blank()
        for table, meta in TABLES.items():
            data[table] = [
                {field: clean(row.get(field, '')) for field in meta['fields']}
                for row in raw.get(table, [])
                if isinstance(row, dict)
            ]
        return data
    except Exception:
        return None


def load_seed_data():
    json_seed = load_json_seed()
    if json_seed and any(json_seed[table] for table in TABLES):
        return json_seed
    data = blank()
    data['Machines'] = load_csv('Machines', MACHINES)
    data['PM_Tasks'] = load_csv('PM_Tasks', TASKS)
    data['Completion_Log'] = load_csv('Completion_Log', LOGS)
    return data


def insert_row(conn, table, row):
    meta = TABLES[table]
    fields = meta['fields']
    values = [clean(row.get(field, '')) for field in fields]
    placeholders = ','.join('?' for _ in fields)
    columns = ','.join(quote_ident(field) for field in fields)
    conn.execute(f'INSERT INTO {quote_ident(meta["sqlite"])} ({columns}) VALUES ({placeholders})', values)


def replace_table(conn, table, rows):
    meta = TABLES[table]
    conn.execute(f'DELETE FROM {quote_ident(meta["sqlite"])}')
    for row in rows:
        if clean(row.get(meta['key'])):
            insert_row(conn, table, row)


def seed_if_needed(conn, created):
    if not created:
        return
    data = load_seed_data()
    for table, rows in data.items():
        replace_table(conn, table, rows)
    conn.commit()


def init_db():
    created = not os.path.exists(DB_FILE)
    conn = db()
    create_schema(conn)
    seed_if_needed(conn, created)
    conn.close()


def load():
    init_db()
    data = blank()
    with db() as conn:
        for table, meta in TABLES.items():
            rows = conn.execute(f'SELECT * FROM {quote_ident(meta["sqlite"])} ORDER BY rowid').fetchall()
            data[table] = [{field: clean(row[field]) for field in meta['fields']} for row in rows]
    return data


def save(data):
    init_db()
    with db() as conn:
        for table in TABLES:
            replace_table(conn, table, data.get(table, []))
        conn.commit()


def add_record(table, row):
    init_db()
    with db() as conn:
        insert_row(conn, table, row)
        conn.commit()


def active(row):
    return clean(row.get('Active (Y/N)', 'Y')).upper() != 'N'


def find(rows, key, value):
    value = clean(value)
    for row in rows:
        if clean(row.get(key)) == value:
            return row
    return None


def row_matches(row, query):
    needle = clean(query).lower()
    if not needle:
        return True
    return any(needle in clean(value).lower() for value in row.values())


def machine_matches(machine, data, query):
    if row_matches(machine, query):
        return True
    machine_id = clean(machine.get('Machine ID'))
    related_tasks = [task for task in data['PM_Tasks'] if clean(task.get('Machine ID')) == machine_id]
    return any(row_matches(task, query) for task in related_tasks)


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


def export_nav():
    return (
        "<a class='btn' href='/export/Machines.csv'>Machines CSV</a>"
        "<a class='btn' href='/export/PM_Tasks.csv'>PM Tasks CSV</a>"
        "<a class='btn' href='/export/Completion_Log.csv'>Completion Log CSV</a>"
    )


def page(title, body):
    settings = load_settings()
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{h(title)}</title><style>
:root{{--bg:#080d12;--top:#0b1118;--side:#101821;--panel:#111a23;--panel2:#172330;--panel3:#1d2a37;--line:#2c3b4a;--line2:#405467;--text:#e6edf4;--muted:#9aa8b6;--muted2:#708294;--orange:#ff8a1c;--orange2:#d86b00;--danger:#ff5d5d;}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif;font-size:14px}}a{{color:var(--text);text-decoration:none}}a:hover{{color:#fff}}.shell{{display:grid;grid-template-columns:285px 1fr;grid-template-rows:48px calc(100vh - 48px);min-height:100vh}}header{{grid-column:1/3;background:#080d12;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;padding:7px 12px}}.brand{{display:flex;align-items:center;font-size:25px;font-weight:800;letter-spacing:.01em;min-width:196px}}.brand:before{{content:"◆";color:var(--orange);font-size:24px;margin-right:10px;transform:rotate(45deg)}}.brand span{{color:var(--orange)}}.top-status{{flex:1;height:33px;border:1px solid var(--line2);background:#05090d;border-radius:4px;color:#b8c2cd;display:flex;align-items:center;padding:0 12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.top-actions{{display:flex;gap:8px}}.side{{grid-row:2;background:var(--side);border-right:1px solid #1f2c38;overflow:auto}}.side-title{{height:39px;background:#15202b;color:#a7b2bf;text-transform:uppercase;font-size:12px;letter-spacing:.05em;display:flex;align-items:center;padding:0 14px}}nav{{padding:12px}}nav a{{display:flex;align-items:center;gap:10px;color:#aab5c2;border:1px solid transparent;border-radius:5px;padding:11px 12px;margin-bottom:7px}}nav a:hover{{background:#182534;border-color:#33485a;color:#eaf0f6}}nav a.primary{{background:var(--orange);color:#05090d;border-color:var(--orange);justify-content:center;font-weight:700}}.side-foot{{position:absolute;bottom:12px;left:12px;width:260px;color:var(--muted2);font-size:12px}}main{{grid-column:2;grid-row:2;display:grid;grid-template-columns:minmax(560px,1fr) 420px;gap:0;min-height:0}}.work{{padding:14px 20px 24px;overflow:auto}}.details{{background:#0b1118;border-left:1px solid #1f2c38;padding:18px 20px;overflow:auto}}h1{{font-size:25px;margin:8px 0 14px;font-weight:800}}h2{{font-size:21px;margin:0 0 12px}}p{{line-height:1.45}}.toolbar{{display:flex;gap:12px;margin:0 0 14px;flex-wrap:wrap}}.searchbox{{height:33px;flex:1;min-width:260px;border:1px solid var(--line2);background:#05090d;color:var(--text);border-radius:4px;padding:0 12px}}.card{{background:transparent;border:0;padding:0;margin:0 0 18px;box-shadow:none}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(160px,1fr));gap:12px;margin-bottom:18px}}.grid .card{{background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:14px 16px}}.grid .card h2{{font-size:27px;margin:0 0 3px}}.grid .card p{{margin:0;color:var(--muted);text-transform:uppercase;font-size:12px;letter-spacing:.04em}}table{{width:100%;border-collapse:separate;border-spacing:0}}th{{background:#1b2a38;color:#aab7c5;font-size:12px;font-weight:500;text-align:left;padding:11px 10px}}td{{background:#101820;border-bottom:5px solid #080d12;color:#dce4ec;padding:12px 10px;vertical-align:top}}tr:hover td{{background:#1b2a38}}td a{{color:#f0f4f8}}.muted{{color:var(--muted)}}.notice{{border:1px solid var(--orange);background:#1a1309;color:#ffd8af;border-radius:4px;padding:10px 12px;margin-bottom:14px}}button,.btn{{border:1px solid var(--line2);background:linear-gradient(#243344,#1b2938);color:#e6edf4;border-radius:4px;padding:9px 16px;font-weight:600;cursor:pointer;display:inline-block}}button:hover,.btn:hover{{background:#2b3d50;color:#fff}}button[type=submit],.btn.primary{{background:var(--orange);border-color:var(--orange);color:#080d12}}button[type=submit]:hover,.btn.primary:hover{{background:#ff982f;color:#05090d}}.danger{{border-color:#b74141;color:#ffb3b3;background:#151014}}label{{display:block;color:#a9b5c1;font-size:12px;margin:8px 0 6px}}input,select,textarea{{width:100%;background:#070b10;border:1px solid var(--line2);border-radius:4px;color:#e6edf4;padding:9px 10px;outline:none}}input:focus,select:focus,textarea:focus{{border-color:var(--orange)}}textarea{{min-height:78px}}.right{{color:var(--muted);font-size:12px}}.meta{{border-top:1px solid #243341;margin-top:18px;padding-top:16px}}.meta-row{{display:grid;grid-template-columns:140px 1fr;gap:12px;margin:10px 0;color:#cdd6df}}.meta-row span:first-child{{color:var(--muted)}}.panel-preview{{height:190px;border:1px solid var(--line);background:#05090d;border-radius:5px;margin-bottom:20px;display:flex;align-items:center;justify-content:center;color:#536273}}.panel-preview:before{{content:"PM";border:2px solid var(--orange);border-radius:50%;width:62px;height:62px;display:flex;align-items:center;justify-content:center;color:var(--orange);font-weight:800}}
@media(max-width:1050px){{.shell{{display:block}}header{{position:sticky;top:0;z-index:2}}.side{{border-right:0}}.side-foot{{position:static;width:auto;margin:20px 12px}}main{{display:block}}.details{{border-left:0;border-top:1px solid #1f2c38}}.grid{{grid-template-columns:1fr}}.top-status{{display:none}}}}
</style></head><body><div class="shell"><header><div class="brand">PM<span>Tracker</span></div><div class="top-status">Host {h(settings['host'])} | Port {h(settings['port'])} | SQLite runtime | Preventive maintenance command center</div><div class="top-actions"><a class="btn" href="/settings">Health</a><a class="btn" href="/exports">Exports</a><a class="btn primary" href="/machines/new">Add Machine</a></div></header><aside class="side"><div class="side-title">Modules</div><nav><a class="primary" href="/">Dashboard</a><a href="/machines/new">Add Machine</a><a href="/tasks/new">Add PM Task</a><a href="/completions">Completion Log</a><a href="/exports">Exports</a><a href="/settings">Host / Port</a></nav><div class="side-foot">Ready. Generic PM tracker shell with SQLite runtime data and header-only import templates.</div></aside><main><section class="work">{body}</section><aside class="details"><div class="panel-preview"></div><h2>PM Tracker</h2><p class="muted">Machine records, task schedules, completion history, exports, and local host settings.</p><div class="meta"><div class="meta-row"><span>Runtime data</span><div>{h(DB_FILE)}</div></div><div class="meta-row"><span>Settings</span><div>{h(SETTINGS_FILE)}</div></div><div class="meta-row"><span>CSV source</span><div>data folder templates</div></div><div class="meta-row"><span>Status</span><div>Local first</div></div></div></aside></main></div></body></html>'''


@app.route('/')
def home():
    data = load()
    query = clean(request.args.get('q'))
    machines = [m for m in data['Machines'] if active(m)]
    tasks = [t for t in data['PM_Tasks'] if active(t)]
    filtered = [m for m in machines if machine_matches(m, data, query)]
    rows = ''.join(f"<tr><td><a href='/machine/{h(m['Machine ID'])}'>{h(m['Machine Name'])}</a></td><td>{h(m['Machine ID'])}</td><td>{h(m['Department'])}</td><td>{h(m['Location'])}</td><td>{h(m['Criticality'])}</td></tr>" for m in filtered)
    if not rows:
        rows = "<tr><td colspan='5' class='muted'>No matching machines.</td></tr>"
    search_note = f"<p class='muted'>Search filter: {h(query)}</p>" if query else ""
    return page('PM Tracker', f"<form class='toolbar' method='get' action='/'><input class='searchbox' name='q' value='{h(query)}' placeholder='Search machine, task, department, location, metadata...'><button>Search</button><a class='btn' href='/'>Clear</a><a class='btn primary' href='/tasks/new'>Add Task</a></form><h1>Preventive Maintenance Tracker</h1>{search_note}<div class='grid'><div class='card'><h2>{len(machines)}</h2><p>Active machines</p></div><div class='card'><h2>{len(tasks)}</h2><p>Active PM tasks</p></div><div class='card'><h2>{len(data['Completion_Log'])}</h2><p>Completion records</p></div></div><div class='card'><h2>Machines</h2><table><tr><th>Machine</th><th>ID</th><th>Department</th><th>Location</th><th>Criticality</th></tr>{rows}</table></div>")


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    current = load_settings()
    msg = ''
    if request.method == 'POST':
        try:
            new = save_settings(request.form.get('host'), request.form.get('port'))
            msg = f"<p class='muted'>Saved. Restart the app for server binding changes to take effect. New setting: {h(new['host'])} port {h(new['port'])}.</p>"
            current = new
        except Exception as exc:
            msg = f"<p class='muted'>Could not save settings: {h(exc)}</p>"
    body = f"<h1>Host and Port</h1><div class='card'><form method='post'><div class='grid'><label>Host<input name='host' value='{h(current['host'])}'></label><label>Port<input name='port' type='number' min='1' max='65535' value='{h(current['port'])}'></label></div><button>Save Host/Port</button></form>{msg}<p class='muted'>Use 127.0.0.1 for local-only access. Use 0.0.0.0 only when you intentionally want LAN access.</p></div>"
    return page('Host and Port', body)


@app.route('/machine/<machine_id>')
def machine(machine_id):
    data = load()
    machine_row = find(data['Machines'], 'Machine ID', machine_id)
    if not machine_row:
        return page('Not found', '<div class="card">Machine not found.</div>'), 404
    rows = ''
    for task in [t for t in data['PM_Tasks'] if clean(t.get('Machine ID')) == machine_id and active(t)]:
        rows += f"<tr><td>{h(task['Task Name'])}<br><span class='muted'>{h(task['Task ID'])}</span></td><td>{h(task['Task Description'])}</td><td>Every {h(task['Frequency Value'])} {h(task['Frequency Unit (Days/Weeks/Months)'])}</td><td>{h(task['Responsible Role'])}</td><td>{h(next_due(data, task))}</td><td><a href='/complete/{h(task['Task ID'])}'>Log completion</a></td></tr>"
    if not rows:
        rows = "<tr><td colspan='6' class='muted'>No active PM tasks for this machine.</td></tr>"
    body = f"<h1>{h(machine_row['Machine Name'])}</h1><div class='card'><p><b>ID:</b> {h(machine_row['Machine ID'])} | <b>Department:</b> {h(machine_row['Department'])} | <b>Location:</b> {h(machine_row['Location'])} | <b>Criticality:</b> {h(machine_row['Criticality'])}</p><p><b>Manufacturer:</b> {h(machine_row['Manufacturer'])} | <b>Model:</b> {h(machine_row['Model'])} | <b>Serial:</b> {h(machine_row['Serial Number'])} | <b>Asset:</b> {h(machine_row['Asset Tag'])}</p><p>{h(machine_row['Notes'])}</p></div><div class='card'><h2>PM Tasks</h2><table><tr><th>Task</th><th>Description</th><th>Frequency</th><th>Role</th><th>Next Due</th><th></th></tr>{rows}</table></div><p><a class='btn primary' href='/tasks/new?machine_id={h(machine_id)}'>Add Task</a></p>"
    return page(machine_row['Machine Name'], body)


@app.route('/machines/new', methods=['GET', 'POST'])
def add_machine():
    data = load()
    msg = ''
    values = {field: '' for field in MACHINES}
    values['Active (Y/N)'] = 'Y'
    if request.method == 'POST':
        row = {field: clean(request.form.get(field, '')) for field in MACHINES}
        row['Active (Y/N)'] = row['Active (Y/N)'] or 'Y'
        values = row
        if not row['Machine ID'] or not row['Machine Name']:
            msg = "<div class='notice'>Machine ID and Machine Name are required.</div>"
        elif find(data['Machines'], 'Machine ID', row['Machine ID']):
            msg = f"<div class='notice'>Machine ID {h(row['Machine ID'])} already exists. Duplicate machines are blocked.</div>"
        else:
            add_record('Machines', row)
            return redirect(url_for('machine', machine_id=row['Machine ID']))
    fields = ''.join(f"<label>{h(field)}<input name='{h(field)}' value='{h(values.get(field, ''))}'></label>" for field in MACHINES)
    return page('Add Machine', f"<h1>Add Machine</h1>{msg}<div class='card'><form method='post'><div class='grid'>{fields}</div><button>Save Machine</button></form></div>"), (409 if msg and 'already exists' in msg else 200)


@app.route('/tasks/new', methods=['GET', 'POST'])
def add_task():
    data = load()
    selected = clean(request.args.get('machine_id'))
    msg = ''
    values = {field: '' for field in TASKS}
    values['Machine ID'] = selected
    values['Frequency Unit (Days/Weeks/Months)'] = 'Days'
    values['Frequency Value'] = '1'
    values['Active (Y/N)'] = 'Y'
    if request.method == 'POST':
        row = {field: clean(request.form.get(field, '')) for field in TASKS}
        row['Active (Y/N)'] = row['Active (Y/N)'] or 'Y'
        values = row
        selected = row['Machine ID']
        if not row['Task ID'] or not row['Machine ID'] or not row['Task Name']:
            msg = "<div class='notice'>Task ID, Machine ID, and Task Name are required.</div>"
        elif find(data['PM_Tasks'], 'Task ID', row['Task ID']):
            msg = f"<div class='notice'>Task ID {h(row['Task ID'])} already exists. Duplicate tasks are blocked.</div>"
        elif not find(data['Machines'], 'Machine ID', row['Machine ID']):
            msg = f"<div class='notice'>Machine ID {h(row['Machine ID'])} does not exist. Create the machine first.</div>"
        else:
            add_record('PM_Tasks', row)
            return redirect(url_for('machine', machine_id=row['Machine ID']))
    options = ''.join(f"<option value='{h(m['Machine ID'])}' {'selected' if m['Machine ID'] == selected else ''}>{h(m['Machine ID'])} - {h(m['Machine Name'])}</option>" for m in data['Machines'] if active(m))
    body = f"<h1>Add PM Task</h1>{msg}<div class='card'><form method='post'><div class='grid'><label>Task ID<input name='Task ID' value='{h(values['Task ID'])}'></label><label>Machine<select name='Machine ID'>{options}</select></label><label>Task Name<input name='Task Name' value='{h(values['Task Name'])}'></label><label>Frequency Unit<select name='Frequency Unit (Days/Weeks/Months)'><option {'selected' if values['Frequency Unit (Days/Weeks/Months)'] == 'Days' else ''}>Days</option><option {'selected' if values['Frequency Unit (Days/Weeks/Months)'] == 'Weeks' else ''}>Weeks</option><option {'selected' if values['Frequency Unit (Days/Weeks/Months)'] == 'Months' else ''}>Months</option></select></label><label>Frequency Value<input name='Frequency Value' type='number' value='{h(values['Frequency Value'])}'></label><label>Responsible Role<input name='Responsible Role' value='{h(values['Responsible Role'])}'></label><label>Estimated Minutes<input name='Estimated Minutes' type='number' value='{h(values['Estimated Minutes'])}'></label><label>Active (Y/N)<input name='Active (Y/N)' value='{h(values['Active (Y/N)'])}'></label></div><label>Task Description<textarea name='Task Description'>{h(values['Task Description'])}</textarea></label><label>Safety Notes<textarea name='Safety Notes'>{h(values['Safety Notes'])}</textarea></label><button>Save Task</button></form></div>"
    return page('Add Task', body), (409 if msg and 'already exists' in msg else 200)


@app.route('/complete/<task_id>', methods=['GET', 'POST'])
def complete(task_id):
    data = load()
    task = find(data['PM_Tasks'], 'Task ID', task_id)
    if not task:
        return page('Not found', '<div class="card">Task not found.</div>'), 404
    if request.method == 'POST':
        now = datetime.now()
        row = {'Completion ID': log_id(data), 'Machine ID': task['Machine ID'], 'Task ID': task['Task ID'], 'Completed By': clean(request.form.get('Completed By')), 'Completion Date': clean(request.form.get('Completion Date')) or now.date().isoformat(), 'Completion Time': clean(request.form.get('Completion Time')) or now.strftime('%H:%M'), 'Notes': clean(request.form.get('Notes')), 'Pass/Fail': clean(request.form.get('Pass/Fail')) or 'Pass'}
        add_record('Completion_Log', row)
        return redirect(url_for('machine', machine_id=task['Machine ID']))
    body = f"<h1>Log Completion</h1><div class='card'><p>{h(task['Task Name'])} | {h(task['Task ID'])}</p><form method='post'><div class='grid'><label>Completed By<input name='Completed By' required></label><label>Date<input type='date' name='Completion Date' value='{h(date.today().isoformat())}'></label><label>Time<input type='time' name='Completion Time' value='{h(datetime.now().strftime('%H:%M'))}'></label><label>Pass/Fail<select name='Pass/Fail'><option>Pass</option><option>Fail</option></select></label></div><label>Notes<textarea name='Notes'></textarea></label><button>Save Completion</button></form></div>"
    return page('Log Completion', body)


@app.route('/completions')
def completions():
    data = load()
    rows = ''.join(f"<tr><td>{h(r['Completion ID'])}</td><td>{h(r['Completion Date'])}</td><td>{h(r['Completion Time'])}</td><td>{h(r['Machine ID'])}</td><td>{h(r['Task ID'])}</td><td>{h(r['Completed By'])}</td><td>{h(r['Pass/Fail'])}</td><td>{h(r['Notes'])}</td></tr>" for r in reversed(data['Completion_Log']))
    if not rows:
        rows = "<tr><td colspan='8' class='muted'>No completion records.</td></tr>"
    return page('Completions', f"<div class='toolbar'>{export_nav()}</div><h1>Completion Log</h1><div class='card'><table><tr><th>ID</th><th>Date</th><th>Time</th><th>Machine</th><th>Task</th><th>By</th><th>Result</th><th>Notes</th></tr>{rows}</table></div>")


@app.route('/exports')
def exports():
    return page('Exports', f"<h1>Exports</h1><p class='muted'>Download current SQLite runtime tables as CSV.</p><div class='toolbar'>{export_nav()}</div>")


@app.route('/export/<table>.csv')
def export_csv(table):
    fields = TABLES.get(table, {}).get('fields')
    if not fields:
        return Response('Unknown table', status=404)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(load()[table])
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={table}.csv'})


if __name__ == '__main__':
    settings = load_settings()
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    print(f"PM Tracker starting on host {settings['host']} port {settings['port']}")
    app.run(debug=debug, host=settings['host'], port=settings['port'])
