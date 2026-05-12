import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from forge.core.context_router import available_actions, breadcrumb, module_names
from forge.work_order_builder.workmanship_rules import prompt_placeholder, suggest_rules


def labels(actions):
    return [action.label for action in actions]


def keys(actions):
    return [action.key for action in actions]


def test_context_router_filters_missing_required_fields():
    actions = available_actions('part', {'part_number': 'P-100'})
    assert 'open_jobs' in keys(actions)
    assert 'open_work_orders' in keys(actions)
    assert 'open_customer_requirements' not in keys(actions)


def test_context_router_includes_customer_actions_when_customer_present():
    actions = available_actions('part', {'part_number': 'P-100', 'customer_id': 'CUST-1'})
    assert 'open_customer_requirements' in keys(actions)
    assert 'Open FAI / inspection' in labels(actions)


def test_breadcrumb_uses_record_identity():
    assert breadcrumb('machine', {'machine_id': 'LASER-1'}) == ['Dashboard', 'Machine / PM', 'LASER-1']


def test_module_names_are_unique_and_include_quality():
    names = list(module_names())
    assert len(names) == len(set(names))
    assert 'quality' in names
    assert 'work_order_builder' in names


def test_workmanship_rules_prioritize_customer_specific_requirements():
    matches = suggest_rules('Purchase order says deburr all edges after laser cut.', 'laser')
    assert matches[0].key == 'customer_requirement_precedence'
    assert 'deburr_all_edges_callout' in keys(matches)
    assert 'laser_default_edge_condition' in keys(matches)


def test_workmanship_rules_filter_by_operation_type():
    matches = suggest_rules('Welded assembly has loose spatter near powder coat surface.', 'welding')
    assert 'weld_cleanup' in keys(matches)
    assert 'surface_condition' not in keys(matches)


def test_prompt_placeholder_returns_operation_specific_guidance():
    assert 'Laser-cut edges' in prompt_placeholder('laser') or 'laser-cut edges' in prompt_placeholder('laser')
    assert 'drawing notes' in prompt_placeholder('unknown').lower()
