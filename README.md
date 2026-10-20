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
