# PM Tracker / Forge Manufacturing Suite Module Map

This repository starts as a generic PM Tracker, but the structure reserves the manufacturing spine needed for a larger Forge-style system.

Design rules:
- Do not add fake production records, fake customers, fake machines, fake people, fake parts, or fake jobs.
- Keep modules tactical, functional, and easy to navigate.
- Right-click behavior should expose logical next steps for the selected record.
- Modules should connect related manufacturing records instead of forcing users to hunt through separate screens.
- Drawing, customer, and specification requirements must drive work order/routing instructions.

## Core module spine

```text
forge/
  core/                 app shell, database, permissions, audit, search, context routing
  assets/               machines, equipment, PM tasks, completions, downtime, resources
  parts/                part master, revisions, drawings, BOMs, specs, customer callouts
  jobs/                 job tracker, work orders, routings, labor/status, travelers
  work_order_builder/   operation deduction, routing notes, workmanship rules, prompts
  quality/              FAI, inspection, NCR, RMA, DMR, deviations, CAPA, audits
  inventory/            materials, lots, stock movement, shortages, allocations
  purchasing/           vendors, purchase orders, receiving, incoming inspection
  shipping/             packing, shipments, labels, freight
  sales/                customers, quotes, order review, customer requirements
  scheduling/           production schedule, machine schedule, MRP, capacity
  integrations/         CSV, XLSX, API, future EDI mappings
  automation/           recurring tasks, reminders, notifications, scheduled imports
  finance_lite/         costing, job cost summaries, ledger-ready exports
  docs/                 work instructions, templates, specifications
```

## Right-click routing principle

Right-click means: what can I do with this record, and where does this record logically connect?

Examples:
- Part Tracker can route into Job Tracker, Work Order/Routing, Drawing/PDM, FAI, NCR/RMA/Deviation, customer requirements, and copy actions.
- Job Tracker can route into parts, work order, routing operations, machine/resource, quality records, shipping/order records, and copy actions.
- Work Order can route into part, drawing, customer requirements, operation notes, inspection plan, machine/resource, and copy actions.
- Machine/PM can route into jobs run on the machine, parts commonly run there, PM history, downtime, machine-related quality records, and copy actions.
- Quality records can route into part, job, drawing, customer, deviation/CAPA/RMA chains, and copy actions.

## Build order

1. core
2. assets
3. parts
4. jobs
5. work_order_builder
6. quality
7. inventory
8. purchasing
9. shipping
10. scheduling
11. sales
12. integrations
13. automation
14. finance_lite

Accounting, payroll, and full EDI are downstream. The first serious product spine is parts, jobs, work orders, quality, machines, and inventory.
