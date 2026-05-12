"""Default workmanship rules used by the work order builder.

These rules are based on the uploaded surface and edge integrity specification.
Customer drawings, purchase order requirements, customer specifications, approved samples,
and job-specific instructions must override these defaults when they are more specific.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class WorkmanshipRule:
    key: str
    trigger_terms: tuple[str, ...]
    operation_types: tuple[str, ...]
    suggested_note: str
    priority: int = 50


DEFAULT_RULES: List[WorkmanshipRule] = [
    WorkmanshipRule(
        key="customer_requirement_precedence",
        trigger_terms=("customer requirement", "drawing note", "purchase order", "approved sample", "specification"),
        operation_types=("order_review", "work_order", "inspection"),
        suggested_note=(
            "Review customer, drawing, purchase order, approved sample, and job-specific requirements. "
            "Apply the most specific documented requirement when it exceeds the default workmanship standard."
        ),
        priority=10,
    ),
    WorkmanshipRule(
        key="deburr_all_edges_callout",
        trigger_terms=("deburr all edges", "remove burrs", "break all edges", "edge break", "no sharp edges"),
        operation_types=("laser", "machining", "secondary", "inspection"),
        suggested_note=(
            "Drawing/customer callout requires edge conditioning. Remove harmful sharpness, loose burrs, and loose material "
            "from applicable edges without changing required geometry, fit, or dimensional conformance."
        ),
        priority=15,
    ),
    WorkmanshipRule(
        key="laser_default_edge_condition",
        trigger_terms=("laser", "laser cut", "profile cut"),
        operation_types=("laser", "inspection"),
        suggested_note=(
            "Laser-cut edges are acceptable as-cut unless sharpness, loose burrs, slag, fit, function, coating, welding, "
            "safe handling, or downstream processing requires cleanup. Do not add unnecessary secondary finishing."
        ),
        priority=30,
    ),
    WorkmanshipRule(
        key="holes_slots_counterbores",
        trigger_terms=("hole", "slot", "counterbore", "countersink", "thread"),
        operation_types=("laser", "machining", "inspection"),
        suggested_note=(
            "Verify holes, slots, counterbores, countersinks, and threaded features are free of burrs or loose material "
            "that could affect assembly, thread engagement, sealing, coating, safe handling, or intended function."
        ),
        priority=35,
    ),
    WorkmanshipRule(
        key="surface_condition",
        trigger_terms=("surface", "cosmetic", "finish", "powder coat", "paint", "coating"),
        operation_types=("forming", "welding", "blast", "paint", "powder_coat", "inspection", "packaging"),
        suggested_note=(
            "Protect surfaces from rejectable scratches, dents, gouges, pits, contamination, loose slag, loose spatter, "
            "or visible damage that could affect coating, fit, function, appearance, or downstream processing."
        ),
        priority=40,
    ),
    WorkmanshipRule(
        key="weld_cleanup",
        trigger_terms=("weld", "weldment", "welded assembly", "spatter", "slag"),
        operation_types=("welding", "grind", "inspection"),
        suggested_note=(
            "Verify weld size, location, length, and profile per drawing. Remove loose slag, loose spatter, and harmful sharpness. "
            "Do not blend or grind welds in a way that reduces required weld size or function unless specifically allowed."
        ),
        priority=25,
    ),
    WorkmanshipRule(
        key="tumbling_media_control",
        trigger_terms=("tumble", "vibratory", "media"),
        operation_types=("secondary", "inspection"),
        suggested_note=(
            "After tumbling or media processing, inspect for trapped media, part damage, unacceptable edge change, "
            "or nonconformance before release to the next operation."
        ),
        priority=45,
    ),
]


def suggest_rules(text: str, operation_type: str | None = None) -> List[WorkmanshipRule]:
    """Return workmanship rules triggered by drawing/spec/job text."""
    haystack = (text or "").lower()
    operation = (operation_type or "").lower()
    matches = []
    for rule in DEFAULT_RULES:
        term_hit = any(term in haystack for term in rule.trigger_terms)
        is_global_override = rule.key == "customer_requirement_precedence"
        op_hit = not operation or operation in rule.operation_types or is_global_override
        if term_hit and op_hit:
            matches.append(rule)
    return sorted(matches, key=lambda r: r.priority)


def prompt_placeholder(operation_type: str) -> str:
    """Return an intelligent placeholder for operation note fields."""
    operation = (operation_type or "").lower()
    examples = {
        "laser": "Example: Drawing calls out deburr all edges. Add note to remove harmful sharpness, loose burrs, or slag from laser-cut edges where required for handling, fit, coating, or downstream processing.",
        "machining": "Example: Machine specified features per current drawing revision. Deburr machined holes/edges only as required without altering required geometry or tolerance.",
        "welding": "Example: Weld per drawing size, length, and location. Remove loose slag/spatter and inspect for cracks or visible workmanship defects before next operation.",
        "powder_coat": "Example: Verify surfaces are free of contamination, loose burrs, loose slag, and damage that could affect coating adhesion or appearance.",
        "inspection": "Example: Inspect drawing/customer callouts first. Where no specific standard exists, verify safe handling, fit, function, surface condition, and edge condition using documented workmanship rules.",
    }
    return examples.get(operation, "Example: Add clear technical instructions for this operation based on drawing notes, customer requirements, material, feature geometry, and downstream processing needs.")
