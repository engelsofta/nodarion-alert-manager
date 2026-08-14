"""Authenticated panel API."""

from __future__ import annotations

from aiohttp import web
from homeassistant.components.http import HomeAssistantView

from .const import DOMAIN
from .manager import PagerManager


class PagerView(HomeAssistantView):
    """Read and mutate Pager configuration."""

    url = f"/api/{DOMAIN}"
    name = f"api:{DOMAIN}"
    requires_auth = True

    def _manager(self, request: web.Request) -> PagerManager | None:
        return request.app["hass"].data.get(DOMAIN, {}).get("manager")

    def _admin(self, request: web.Request) -> bool:
        user = request.get("hass_user")
        return bool(user and user.is_admin)

    async def get(self, request: web.Request) -> web.Response:
        if not self._admin(request):
            return self.json_message("Administrator access required", 403)
        manager = self._manager(request)
        if manager is None:
            return self.json_message("Integration is not loaded", 503)
        scope = request.query.get("scope", "full")
        offset = max(0, int(request.query.get("offset", 0)))
        limit = min(500, max(1, int(request.query.get("limit", 100))))
        return self.json(manager.frontend_state(scope=scope, offset=offset, limit=limit))

    async def post(self, request: web.Request) -> web.Response:
        manager = self._manager(request)
        if manager is None:
            return self.json_message("Integration is not loaded", 503)
        if not self._admin(request):
            return self.json_message("Administrator access required", 403)
        try:
            data = await request.json()
            action = data.get("action")
            if action == "save_rule":
                await manager.async_save_rule(data.get("rule") or {})
            elif action == "delete_rule":
                await manager.async_delete_rule(str(data["rule_id"]))
            elif action == "toggle_rule":
                await manager.async_toggle_rule(str(data["rule_id"]), bool(data["enabled"]))
            elif action == "pause_rule":
                await manager.async_pause_rule(str(data["rule_id"]), float(data.get("seconds", 0)))
            elif action == "duplicate_rule":
                await manager.async_duplicate_rule(str(data["rule_id"]))
            elif action == "acknowledge":
                await manager.async_acknowledge(str(data["alert_id"]))
            elif action == "resolve":
                await manager.async_resolve(str(data["alert_id"]))
            elif action == "settings":
                await manager.async_update_settings(data.get("settings") or {})
            elif action == "test_notification":
                await manager.async_test_notification_target(str(data["target_id"]))
            elif action == "comment":
                user = request.get("hass_user")
                await manager.async_comment(str(data["alert_id"]), str(data.get("comment", "")), getattr(user, "id", None))
            elif action == "maintenance":
                await manager.async_set_maintenance(float(data.get("seconds", 0)))
            elif action == "import_rules":
                await manager.async_import_rules(data.get("rules", []), bool(data.get("replace", False)))
            elif action == "export_rules":
                return self.json({"schema_version": 2, "rules": manager.export_rules()})
            elif action == "clear_history":
                manager.history.clear()
                await manager._async_save()
            else:
                return self.json_message("Unknown action", 400)
        except (KeyError, TypeError, ValueError) as err:
            return self.json_message(str(err) or "Invalid request", 400)
        return self.json(manager.frontend_state())
