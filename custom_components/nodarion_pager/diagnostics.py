"""Diagnostics for Nodarion Pager."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

TO_REDACT = {
    "activity_id",
    "comment",
    "critical_text_template",
    "entity_id",
    "last_payload",
    "message_template",
    "name",
    "notification_targets",
    "notified_targets",
    "progress_entity",
    "remaining_time_entity",
    "rule_name",
    "title",
    "update_entities",
    "user_id",
    "value",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return privacy-conscious integration diagnostics."""
    manager = entry.runtime_data
    return {
        "entry": {"entry_id": entry.entry_id, "version": entry.version},
        "summary": manager.diagnostics(),
        "rules": async_redact_data(manager.export_rules(), TO_REDACT),
        "alerts": async_redact_data(list(manager.alerts.values()), TO_REDACT),
        "runtime": async_redact_data(manager.runtime, TO_REDACT),
        "live_activities": async_redact_data(
            [activity.as_dict() for activity in manager.live_activities.values()], TO_REDACT
        ),
        "activity_runtime": async_redact_data(manager.activity_runtime, TO_REDACT),
    }
