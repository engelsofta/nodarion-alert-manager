"""WebSocket push updates for Nodarion Pager."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import SIGNAL_UPDATE


@websocket_api.websocket_command({vol.Required("type"): "nodarion_pager/subscribe"})
@websocket_api.require_admin
@callback
def websocket_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Subscribe an administrator to lightweight Pager updates."""
    connection.send_result(msg["id"])

    @callback
    def forward(payload: dict) -> None:
        connection.send_message(websocket_api.event_message(msg["id"], payload))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_UPDATE, forward
    )
