"""Tests for Pager's standalone rule comparisons."""

from custom_components.nodarion_pager.models import Rule, matches, matches_condition


def rule(operator="gt", value=10, upper=None, hysteresis=0):
    return Rule.from_dict({"name": "Test", "entity_id": "sensor.test", "operator": operator, "value": value, "value_upper": upper, "hysteresis": hysteresis})


def test_numeric_operators():
    assert matches(rule("gt"), "11")
    assert matches(rule("gte"), "10")
    assert matches(rule("lt"), "9")
    assert matches(rule("lte"), "10")
    assert matches(rule("between", 10, 20), "15")
    assert matches(rule("outside", 10, 20), "21")


def test_string_operators_are_case_insensitive():
    assert matches(rule("eq", "Alarm"), "alarm")
    assert matches(rule("ne", "off"), "on")


def test_hysteresis_keeps_active_rule_until_lower_reset_point():
    item = rule("gt", 10, hysteresis=2)
    assert matches(item, 9, resetting=True)
    assert not matches(item, 8, resetting=True)


def test_validation_rejects_invalid_rule():
    try:
        Rule.from_dict({"name": "Bad", "entity_id": "sensor.x", "operator": "wat"})
    except ValueError:
        return
    raise AssertionError("invalid operator accepted")


def test_binary_and_fault_rule_types():
    assert matches(rule("eq", "on"), "on")
    fault = Rule.from_dict({"name": "Fault", "entity_id": "binary_sensor.fault", "kind": "fault", "operator": "eq", "value": "on"})
    assert fault.kind == "fault"
    assert matches(fault, "on")


def test_rule_notification_targets_round_trip_and_legacy_default():
    legacy = rule()
    assert legacy.notification_targets is None

    item = Rule.from_dict({
        "name": "Targeted", "entity_id": "sensor.targeted", "operator": "gt",
        "value": 10, "notification_targets": ["entity:notify.phone", "service:notify.telegram"],
    })
    assert item.as_dict()["notification_targets"] == [
        "entity:notify.phone", "service:notify.telegram",
    ]


def test_heartbeat_requires_a_positive_timeout():
    heartbeat = Rule.from_dict({
        "name": "PLC heartbeat", "entity_id": "sensor.plc_timer",
        "kind": "heartbeat", "duration": 300,
    })
    assert heartbeat.kind == "heartbeat"
    assert heartbeat.duration == 300

    try:
        Rule.from_dict({
            "name": "Bad heartbeat", "entity_id": "sensor.plc_timer",
            "kind": "heartbeat", "duration": 0,
        })
    except ValueError:
        return
    raise AssertionError("heartbeat without timeout accepted")


def test_unavailable_delay_defaults_to_one_minute_and_is_configurable():
    assert rule().unavailable_delay == 60
    configured = Rule.from_dict({
        "name": "Delayed outage", "entity_id": "sensor.delayed",
        "operator": "eq", "value": "on", "unavailable_delay": 180,
    })
    assert configured.unavailable_delay == 180
    assert configured.as_dict()["unavailable_delay"] == 180


def test_extended_rule_fields_round_trip():
    item = Rule.from_dict({
        "name": "Scheduled", "entity_id": "sensor.main", "operator": "gt", "value": 10,
        "conditions": [{"entity_id": "switch.pump", "operator": "eq", "value": "on"}],
        "condition_mode": "and", "schedule": {"weekdays": [0, 1], "start": "08:00", "end": "18:00"},
        "escalation": [{"after": 600, "severity": "critical"}],
    })
    saved = item.as_dict()
    assert saved["conditions"][0]["entity_id"] == "switch.pump"
    assert saved["schedule"]["weekdays"] == [0, 1]
    assert saved["escalation"][0]["after"] == 600


def test_additional_condition_comparison():
    assert matches_condition({"entity_id": "switch.pump", "operator": "eq", "value": "on"}, "ON")
