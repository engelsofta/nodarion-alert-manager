"""Diagnostics for Nodarion Pager."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from .const import DOMAIN

TO_REDACT = {"entity_id", "rule_name", "name", "value", "comment", "user_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return privacy-conscious integration diagnostics."""
    manager = hass.data[DOMAIN]["manager"]
    return {
        "entry": {"entry_id": entry.entry_id, "version": entry.version},
        "summary": manager.diagnostics(),
        "rules": async_redact_data(manager.export_rules(), TO_REDACT),
        "alerts": async_redact_data(list(manager.alerts.values()), TO_REDACT),
        "runtime": async_redact_data(manager.runtime, TO_REDACT),
    }
