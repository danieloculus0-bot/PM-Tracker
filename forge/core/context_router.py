"""Context-aware routing rules for Forge-style manufacturing modules.

Right-click behavior should expose logical next steps for the selected record.
It should not become a giant generic menu dump.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ContextAction:
    key: str
    label: str
    target_module: str
    intent: str
    requires: tuple[str, ...] = ()


ROUTES: Dict[str, List[ContextAction]] = {
    "part": [
        ContextAction("open_jobs", "Open related jobs", "jobs", "open_related_jobs", ("part_number",)),
        ContextAction("open_work_orders", "Open work orders / routing", "jobs", "open_work_orders", ("part_number",)),
        ContextAction("open_drawing", "Open drawing / PDM record", "parts", "open_drawing", ("part_number",)),
        ContextAction("open_bom", "Open BOM / assembly", "parts", "open_bom", ("part_number",)),
        ContextAction("open_fai", "Open FAI / inspection", "quality", "open_fai", ("part_number",)),
        ContextAction("open_quality", "Open NCR / RMA / deviation", "quality", "open_related_quality", ("part_number",)),
        ContextAction("open_customer_requirements", "Open customer requirements", "sales", "open_customer_requirements", ("customer_id",)),
        ContextAction("copy_part", "Copy part number", "clipboard", "copy", ("part_number",)),
    ],
    "job": [
        ContextAction("open_parts", "Open parts on job", "parts", "open_parts_for_job", ("job_number",)),
        ContextAction("open_work_order", "Open work order", "jobs", "open_work_order", ("job_number",)),
        ContextAction("open_routing", "Open routing operations", "jobs", "open_routing", ("job_number",)),
        ContextAction("open_machine", "Open machine / resource", "assets", "open_resource", ("resource_id",)),
        ContextAction("open_inspection", "Open inspection records", "quality", "open_inspection_for_job", ("job_number",)),
        ContextAction("open_quality", "Open NCR / RMA / deviation", "quality", "open_related_quality", ("job_number",)),
        ContextAction("open_shipping", "Open shipment / order record", "shipping", "open_shipping_for_job", ("job_number",)),
        ContextAction("copy_job", "Copy job number", "clipboard", "copy", ("job_number",)),
    ],
    "work_order": [
        ContextAction("open_part", "Open part", "parts", "open_part", ("part_number",)),
        ContextAction("open_drawing", "Open drawing", "parts", "open_drawing", ("part_number",)),
        ContextAction("open_requirements", "Open customer requirements", "sales", "open_customer_requirements", ("customer_id",)),
        ContextAction("open_operation_notes", "Open operation notes", "work_order_builder", "open_operation_notes", ("work_order_id",)),
        ContextAction("open_inspection_plan", "Open inspection plan", "quality", "open_inspection_plan", ("work_order_id",)),
        ContextAction("open_resource", "Open machine / resource", "assets", "open_resource", ("resource_id",)),
        ContextAction("copy_summary", "Copy operation summary", "clipboard", "copy", ("operation_id",)),
    ],
    "machine": [
        ContextAction("open_jobs", "Open jobs run on this machine", "jobs", "open_jobs_for_machine", ("machine_id",)),
        ContextAction("open_parts", "Open parts commonly run here", "parts", "open_parts_for_machine", ("machine_id",)),
        ContextAction("open_pm_history", "Open PM history", "assets", "open_pm_history", ("machine_id",)),
        ContextAction("open_downtime", "Open downtime / repair history", "assets", "open_downtime", ("machine_id",)),
        ContextAction("open_quality", "Open machine-related quality records", "quality", "open_related_quality", ("machine_id",)),
        ContextAction("copy_machine", "Copy machine ID", "clipboard", "copy", ("machine_id",)),
    ],
    "quality_record": [
        ContextAction("open_part", "Open part", "parts", "open_part", ("part_number",)),
        ContextAction("open_job", "Open job", "jobs", "open_job", ("job_number",)),
        ContextAction("open_drawing", "Open drawing", "parts", "open_drawing", ("part_number",)),
        ContextAction("open_customer", "Open customer", "sales", "open_customer", ("customer_id",)),
        ContextAction("open_chain", "Open deviation / CAPA / RMA chain", "quality", "open_quality_chain", ("quality_record_id",)),
        ContextAction("copy_record", "Copy record number", "clipboard", "copy", ("quality_record_id",)),
    ],
}


def available_actions(record_type: str, record: Optional[dict] = None) -> List[ContextAction]:
    """Return context actions that make sense for a selected record.

    If record data is supplied, actions with missing required fields are filtered out.
    """
    actions = ROUTES.get(record_type, [])
    if record is None:
        return list(actions)
    return [action for action in actions if all(record.get(field) for field in action.requires)]


def breadcrumb(record_type: str, record: Optional[dict] = None) -> List[str]:
    """Return a simple breadcrumb path for the selected module record."""
    labels = {
        "part": "Part Tracker",
        "job": "Job Tracker",
        "work_order": "Work Order",
        "machine": "Machine / PM",
        "quality_record": "Quality Record",
    }
    crumb = ["Dashboard", labels.get(record_type, record_type.replace("_", " ").title())]
    if record:
        for field in ("part_number", "job_number", "work_order_id", "machine_id", "quality_record_id"):
            if record.get(field):
                crumb.append(str(record[field]))
                break
    return crumb


def module_names() -> Iterable[str]:
    """Return module names referenced by the context router."""
    seen = []
    for actions in ROUTES.values():
        for action in actions:
            if action.target_module not in seen:
                seen.append(action.target_module)
    return seen
