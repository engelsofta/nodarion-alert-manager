"""Phone alarm notifications should be cleared when an alert resolves."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest


def _notification_method():
    """Load this method without importing Home Assistant's optional frontend packages."""
    path = Path(__file__).resolve().parents[1] / "custom_components/nodarion_pager/manager.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    manager = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PagerManager")
    method = next(node for node in manager.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "_async_forward_notification")
    namespace = {"Any": Any}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[method.name]


def test_mobile_alert_is_tagged_and_cleared_even_without_resolved_message():
    calls = AsyncMock()
    manager = SimpleNamespace()
    manager.hass = SimpleNamespace(services=SimpleNamespace(async_call=calls))
    manager.settings = {
        "notifications_enabled": True,
        "notify_warning": True,
        "notify_resolved": False,
        "notification_targets": ["service:notify.mobile_app_phone"],
    }
    manager.rules = {
        "rule-1": SimpleNamespace(notification_targets=["service:notify.mobile_app_phone"])
    }
    manager.last_notification_errors = {}
    manager._notification_targets = lambda: [{"id": "service:notify.mobile_app_phone"}]
    manager._entity_name = lambda _: "DNS Querys"
    alert = {
        "id": "alert-1", "rule_id": "rule-1", "entity_id": "sensor.dns",
        "severity": "warning", "mobile_notification_targets": [],
    }

    forward = _notification_method()
    asyncio.run(forward(manager, alert, "alert"))
    asyncio.run(forward(manager, alert, "repeat"))
    asyncio.run(forward(manager, alert, "resolved"))

    assert alert["mobile_notification_targets"] == ["service:notify.mobile_app_phone"]
    assert calls.await_count == 3
    assert calls.await_args_list[0].args[2]["data"] == {"tag": "nodarion_pager_alert-1"}
    assert calls.await_args_list[1].args[2]["data"] == {"tag": "nodarion_pager_alert-1"}
    assert calls.await_args_list[2].args[2] == {
        "message": "clear_notification", "data": {"tag": "nodarion_pager_alert-1"}
    }


@pytest.mark.parametrize("severity", ["info", "warning"])
def test_persistent_notification_target_is_dismissed_on_resolution(severity):
    calls = AsyncMock()
    manager = SimpleNamespace(
        hass=SimpleNamespace(services=SimpleNamespace(async_call=calls)),
        settings={
            "notifications_enabled": True, "notify_info": True, "notify_warning": True,
            "notify_resolved": True,
            "notification_targets": ["service:notify.persistent_notification"],
        },
        rules={
            "rule-1": SimpleNamespace(
                notification_targets=["service:notify.persistent_notification"]
            )
        },
        last_notification_errors={},
    )
    manager._notification_targets = lambda: [{"id": "service:notify.persistent_notification"}]
    manager._entity_name = lambda _: "DNS Querys"
    alert = {
        "id": "alert-1", "rule_id": "rule-1", "entity_id": "sensor.dns",
        "severity": severity, "mobile_notification_targets": [],
        "persistent_notification_sent": False,
    }

    forward = _notification_method()
    asyncio.run(forward(manager, alert, "alert"))
    asyncio.run(forward(manager, alert, "resolved"))

    assert calls.await_count == 2
    assert calls.await_args_list[0].args == (
        "notify", "persistent_notification",
        {"title": "DNS Querys", "message": "Alarm",
         "data": {"notification_id": "nodarion_pager_alert-1"}},
    )
    assert calls.await_args_list[1].args == (
        "persistent_notification", "dismiss",
        {"notification_id": "nodarion_pager_alert-1"},
    )


def test_critical_notifications_remain_after_resolution():
    calls = AsyncMock()
    targets = ["service:notify.mobile_app_phone", "service:notify.persistent_notification"]
    manager = SimpleNamespace(
        hass=SimpleNamespace(services=SimpleNamespace(async_call=calls)),
        settings={
            "notifications_enabled": True, "notify_critical": True,
            "notify_resolved": True, "notification_targets": targets,
        },
        rules={"rule-1": SimpleNamespace(notification_targets=targets)},
        last_notification_errors={},
    )
    manager._notification_targets = lambda: [{"id": target} for target in targets]
    manager._entity_name = lambda _: "DNS Querys"
    alert = {
        "id": "alert-1", "rule_id": "rule-1", "entity_id": "sensor.dns",
        "severity": "critical", "mobile_notification_targets": [],
        "persistent_notification_sent": False,
    }

    forward = _notification_method()
    asyncio.run(forward(manager, alert, "alert"))
    asyncio.run(forward(manager, alert, "resolved"))

    assert calls.await_count == 3
    assert all(call.args[2]["message"] != "clear_notification" for call in calls.await_args_list)
    assert all(call.args[:2] != ("persistent_notification", "dismiss") for call in calls.await_args_list)
