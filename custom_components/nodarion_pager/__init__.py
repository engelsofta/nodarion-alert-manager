"""Nodarion Pager integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .api import PagerView
from .const import DOMAIN, PANEL_TITLE, PANEL_URL, STATIC_URL, VERSION
from .manager import PagerManager
from .websocket import websocket_subscribe

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Register integration actions independently from a config entry."""
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("services_registered"):
        return True

    async def handle_service(call) -> None:
        manager: PagerManager | None = hass.data.get(DOMAIN, {}).get("manager")
        if manager is None:
            return
        if call.service == "acknowledge":
            await manager.async_acknowledge(str(call.data["alert_id"]))
        elif call.service == "resolve":
            await manager.async_resolve(str(call.data["alert_id"]))
        elif call.service == "enable_rule":
            await manager.async_toggle_rule(str(call.data["rule_id"]), True)
        elif call.service == "disable_rule":
            await manager.async_toggle_rule(str(call.data["rule_id"]), False)
        elif call.service == "pause_rule":
            await manager.async_pause_rule(
                str(call.data["rule_id"]), float(call.data.get("seconds", 0))
            )
        elif call.service == "maintenance":
            await manager.async_set_maintenance(float(call.data.get("seconds", 0)))

    for service in (
        "acknowledge",
        "resolve",
        "enable_rule",
        "disable_rule",
        "pause_rule",
        "maintenance",
    ):
        hass.services.async_register(DOMAIN, service, handle_service)
    data["services_registered"] = True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pager and its admin panel."""
    data = hass.data.setdefault(DOMAIN, {})
    manager = PagerManager(hass)
    await manager.async_start()
    entry.runtime_data = manager
    data["manager"] = manager
    if not data.get("api_registered"):
        hass.http.register_view(PagerView)
        websocket_api.async_register_command(hass, websocket_subscribe)
        data["api_registered"] = True
    await _async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Pager."""
    data = hass.data.get(DOMAIN, {})
    manager: PagerManager | None = entry.runtime_data
    if manager:
        await manager.async_stop()
    if data.get("manager") is manager:
        data.pop("manager", None)
    frontend.async_remove_panel(hass, PANEL_URL)
    hass.data.pop(f"{DOMAIN}_panel", None)
    return True


async def _async_register_panel(hass: HomeAssistant) -> None:
    panel_key = f"{DOMAIN}_panel"
    static_key = f"{DOMAIN}_static"
    if hass.data.get(panel_key):
        return
    if not hass.data.get(static_key):
        path = Path(__file__).parent / "frontend"
        await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(path), False)])
        hass.data[static_key] = True
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon="mdi:bell-alert",
        frontend_url_path=PANEL_URL,
        config={"_panel_custom": {
            "name": "engelsoft-nodarion-pager-panel",
            "module_url": f"{STATIC_URL}/nodarion-pager-panel.js?v={VERSION}",
            "embed_iframe": False,
            "trust_external_script": False,
        }},
        require_admin=True,
    )
    hass.data[panel_key] = True
