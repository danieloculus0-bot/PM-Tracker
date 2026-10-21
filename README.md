# PM-Tracker

Standalone maintenance scheduling and work-completion tracking application for equipment and facility operations. It can run without Axiom or JobBOSS².

## Current build state

**Reviewed:** 2026-10-20 · **Inspected main:** `10e8ba3959b5`.

- [PM Tracker smoke](https://github.com/danieloculus0-bot/PM-Tracker/actions/runs/39489953748) — **Passed** at inspected `main`.
- [Build EZ-WMF Windows Server Release](https://github.com/danieloculus0-bot/PM-Tracker/actions/runs/39489953623) — **Passed** at inspected `main`.

Use [live Actions](https://github.com/danieloculus0-bot/PM-Tracker/actions) for changes after this dated verification.

## Working implementation

- Machine inventory, PM task scheduling, completion history, work requests, QR machine pages and data import/export.
- Windows-friendly server and installer packaging, Waitress-based runtime and optional branded site configuration.
- Explicit machine-task safety notes and conditional lockout/tagout reminders; app logic is not machine isolation.

## Run and test

Use the [archived full run/deployment guide](docs/archive/README_2026-10-20_before_refresh.md) for local Flask launch, Windows executable/Server setup, site data import and configuration. Test the actual target-machine work instructions before site use.

## Limitations

- Green packaging tests do not establish a live secured site-server installation or data migration from Excel.
- LOTO reminders do not isolate machinery, prove zero energy, verify training or authorize hazardous maintenance.
- Axiom may contain PM concepts/source snapshots but is not automatically reading from this standalone tracker.

## Next steps

Verify site configuration, database integrity, machine-specific safety references and an explicit optional Axiom integration.

## Documentation

- [Axiom ERP target](https://github.com/danieloculus0-bot/Axiom_Beta)
- [Full historical README, including original setup detail](docs/archive/README_2026-10-20_before_refresh.md)


## Authenticated operation (security remediation)

**Fail closed:** the web application returns HTTP 503 until both
\`PM_SESSION_SECRET\` (a random secret of at least 32 characters) and
\`PM_USERS_JSON\` (server-side accounts) are configured. There is no built-in
user, default password, or anonymous editing. Roles: \`viewer\` (read only),
\`operator\` (record PM work, submit requests), and \`admin\` (also imports
workbooks and closes maintenance requests). Accounts are provisioned by an
administrator, not by client-supplied usernames.

Generate each password hash locally using
\`python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Password: ')))"\`.
Configure \`PM_USERS_JSON\` as a JSON object such as
\`{"technician":{"password_hash":"<output from command>","role":"operator"}}\`.
Supply this JSON and the distinct \`PM_SESSION_SECRET\` through process environment
secrets. Do not commit credentials or unhashed passwords.

Visit \`/login\` to authenticate. Every POST requires the form's hidden CSRF
token. Completion and request submission identities are derived from the
authenticated server session; submitted \`operator_name\` and \`submitted_by\`
values are not trusted.

The sample site binds only to \`127.0.0.1\`. When exposing the application to
a network, place it behind a TLS-terminating reverse proxy and explicitly
set \`PM_TLS_TERMINATED=1\`; this also enables Secure session cookies.
Do not expose the raw HTTP listener on a public network. Recheck user
provisioning and the reverse proxy's access controls before deployment.
The application's login is not an enterprise identity-provider integration;
future SSO and session-expiration controls remain deployment work.
