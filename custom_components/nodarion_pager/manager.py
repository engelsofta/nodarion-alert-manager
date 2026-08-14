"""Persistent entity rule engine for Nodarion Pager."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_SETTINGS,
    DOMAIN,
    EVENT_ACKNOWLEDGED,
    EVENT_ALERT,
    EVENT_RESOLVED,
    SIGNAL_UPDATE,
    STORAGE_KEY,
    STORAGE_VERSION,
    VERSION,
)
from .models import Rule, matches, matches_condition

_LOGGER = logging.getLogger(__name__)
UNAVAILABLE = {"unknown", "unavailable"}


class PagerManager:
    """Own rules, timers, active alarms and history."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.rules: dict[str, Rule] = {}
        self.alerts: dict[str, dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []
        self.runtime: dict[str, dict[str, Any]] = {}
        self.settings = dict(DEFAULT_SETTINGS)
        self._timers: dict[str, Any] = {}
        self._unsub = None
        self._save_task: asyncio.Task | None = None
        self._save_dirty = False
        self._rule_locks: dict[str, asyncio.Lock] = {}
        self.last_notification_errors: dict[str, str] = {}
        self._startup_ready = False
        self._startup_cancel = None
        self._startup_listener = None
        self._schedule_unsub = None

    async def async_start(self) -> None:
        saved = self._migrate(await self.store.async_load() or {})
        self.settings.update(saved.get("settings", {}))
        for raw in saved.get("rules", []):
            try:
                rule = Rule.from_dict(raw)
                self.rules[rule.id] = rule
            except (TypeError, ValueError):
                _LOGGER.warning("Ignoring invalid Pager rule")
        self.alerts = {item["id"]: item for item in saved.get("alerts", []) if item.get("id")}
        self.history = list(saved.get("history", []))
        self.runtime = dict(saved.get("runtime", {}))
        self._schedule_unsub = async_track_time_interval(self.hass, self._schedule_tick, timedelta(minutes=1))
        self._resubscribe()
        if self.hass.is_running:
            self._schedule_startup_evaluation()
        else:
            self._startup_listener = self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, self._home_assistant_started
            )

    async def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
        if self._startup_listener:
            self._startup_listener()
        if self._startup_cancel:
            self._startup_cancel()
        if self._schedule_unsub:
            self._schedule_unsub()
        for cancel in self._timers.values():
            cancel()
        await self._async_save()

    @callback
    def _state_changed(self, event: Event) -> None:
        if not self._startup_ready:
            return
        entity_id = event.data["entity_id"]
        state = event.data.get("new_state")
        for rule in self.rules.values():
            watched = rule.entity_id == entity_id or any(item.get("entity_id") == entity_id for item in rule.conditions)
            if rule.enabled and watched:
                primary_state = state if rule.entity_id == entity_id else self.hass.states.get(rule.entity_id)
                if rule.kind == "heartbeat":
                    if rule.entity_id != entity_id:
                        self.hass.async_create_task(self.async_evaluate(rule, primary_state))
                        continue
                    old_state = event.data.get("old_state")
                    old_value = self._value(rule, old_state)
                    new_value = self._value(rule, state)
                    if old_state is not None and old_value == new_value:
                        continue
                    self.hass.async_create_task(self._async_heartbeat_pulse(rule, state))
                else:
                    self.hass.async_create_task(self.async_evaluate(rule, primary_state))

    @callback
    def _home_assistant_started(self, _event: Event) -> None:
        """Begin the grace period only after Home Assistant itself is ready."""
        self._startup_listener = None
        self._schedule_startup_evaluation()

    @callback
    def _schedule_tick(self, _now) -> None:
        if not self._startup_ready:
            return
        for rule in self.rules.values():
            if rule.enabled:
                self.hass.async_create_task(self.async_evaluate(rule, self.hass.states.get(rule.entity_id)))
        self._refresh_repairs()

    @callback
    def _schedule_startup_evaluation(self) -> None:
        delay = max(0, float(self.settings.get("startup_delay", 60)))

        @callback
        def ready(_now) -> None:
            self._startup_cancel = None
            self._startup_ready = True
            for rule in self.rules.values():
                if rule.enabled:
                    self.hass.async_create_task(
                        self.async_evaluate(rule, self.hass.states.get(rule.entity_id))
                    )
            self._refresh_repairs()

        self._startup_cancel = async_call_later(self.hass, delay, ready)

    def _value(self, rule: Rule, state: State | None) -> Any:
        if state is None:
            return "unavailable"
        return state.attributes.get(rule.attribute) if rule.attribute else state.state

    @staticmethod
    def _migrate(saved: dict[str, Any]) -> dict[str, Any]:
        """Migrate persisted data without discarding older installations."""
        version = int(saved.get("schema_version", 1))
        if version < 2:
            saved.setdefault("settings", {}).setdefault("maintenance_until", None)
            for raw in saved.get("rules", []):
                raw.setdefault("conditions", [])
                raw.setdefault("condition_mode", "and")
                raw.setdefault("schedule", {})
                raw.setdefault("escalation", [])
                raw.setdefault("paused_until", None)
            saved["schema_version"] = 2
        return saved

    def _temporarily_paused(self, rule: Rule) -> bool:
        now = dt_util.now()
        timestamps = [rule.paused_until, self.settings.get("maintenance_until")]
        return any(value and datetime.fromisoformat(value) > now for value in timestamps)

    def _scheduled_now(self, rule: Rule) -> bool:
        schedule = rule.schedule
        if not schedule:
            return True
        now = dt_util.now()
        days = schedule.get("weekdays")
        if isinstance(days, list) and days and now.weekday() not in days:
            return False
        start, end = schedule.get("start"), schedule.get("end")
        current = now.strftime("%H:%M")
        if start and end:
            return start <= current < end if start <= end else current >= start or current < end
        return True

    def _additional_conditions_match(self, rule: Rule) -> bool:
        results = []
        for condition in rule.conditions:
            state = self.hass.states.get(str(condition.get("entity_id", "")))
            value = state.attributes.get(condition.get("attribute")) if state and condition.get("attribute") else (state.state if state else None)
            results.append(matches_condition(condition, value))
        return (all(results) if rule.condition_mode == "and" else any(results)) if results else True

    async def async_evaluate(self, rule: Rule, state: State | None) -> None:
        lock = self._rule_locks.setdefault(rule.id, asyncio.Lock())
        async with lock:
            await self._async_evaluate_locked(rule, state)

    async def _async_evaluate_locked(self, rule: Rule, state: State | None) -> None:
        if self._temporarily_paused(rule) or not self._scheduled_now(rule):
            self._cancel_timer(rule.id)
            return
        if rule.kind == "heartbeat":
            await self._async_evaluate_heartbeat(rule, state)
            return
        actual = self._value(rule, state)
        unavailable = state is None or state.state in UNAVAILABLE or actual is None
        current = self._active_for_rule(rule.id)
        if unavailable:
            if rule.unavailable_behavior == "pause":
                return
            violated = rule.unavailable_behavior == "alert"
            reason = "unavailable"
        else:
            violated = matches(rule, actual, resetting=current is not None) and self._additional_conditions_match(rule)
            reason = "condition"
        rt = self.runtime.setdefault(rule.id, {})
        rt["last_value"] = actual
        rt["last_evaluated"] = dt_util.now().isoformat()
        if violated:
            if current:
                await self._maybe_repeat(rule, current)
                self._schedule_save()
                return
            # A manually resolved or acknowledged condition must not create a
            # fresh alarm until it has genuinely returned to normal once.
            if rt.get("latched"):
                self._schedule_save()
                return
            if rt.get("pending_reason") != reason:
                self._cancel_timer(rule.id)
                rt["pending_since"] = dt_util.now().isoformat()
                rt["pending_reason"] = reason
            elif not rt.get("pending_since"):
                rt["pending_since"] = dt_util.now().isoformat()
            elapsed = (dt_util.now() - datetime.fromisoformat(rt["pending_since"])).total_seconds()
            delay = rule.unavailable_delay if reason == "unavailable" else rule.duration
            remaining = max(0, delay - elapsed)
            if remaining <= 0:
                await self._trigger(rule, actual, reason)
            else:
                self._schedule_timer(rule, remaining)
        else:
            rt.pop("pending_since", None)
            rt.pop("pending_reason", None)
            rt.pop("latched", None)
            self._cancel_timer(rule.id)
            if current and (rule.reset_mode == "automatic" or rule.kind == "fault"):
                await self.async_resolve(current["id"], "condition_cleared")
        self._schedule_save()

    async def _async_heartbeat_pulse(self, rule: Rule, state: State | None) -> None:
        """Reset a heartbeat clock after the monitored value really changed."""
        lock = self._rule_locks.setdefault(rule.id, asyncio.Lock())
        async with lock:
            rt = self.runtime.setdefault(rule.id, {})
            rt["last_heartbeat"] = dt_util.now().isoformat()
            rt.pop("latched", None)
            await self._async_evaluate_heartbeat(rule, state)

    async def _async_evaluate_heartbeat(self, rule: Rule, state: State | None) -> None:
        """Alarm when an entity value has not changed within its timeout."""
        actual = self._value(rule, state)
        unavailable = state is None or state.state in UNAVAILABLE or actual is None
        rt = self.runtime.setdefault(rule.id, {})
        rt["last_value"] = actual
        rt["last_evaluated"] = dt_util.now().isoformat()
        current = self._active_for_rule(rule.id)

        if unavailable:
            if rule.unavailable_behavior == "pause":
                self._cancel_timer(rule.id)
                self._schedule_save()
                return
            if rule.unavailable_behavior == "alert":
                if not current and not rt.get("latched"):
                    if rt.get("pending_reason") != "unavailable":
                        self._cancel_timer(rule.id)
                        rt["pending_since"] = dt_util.now().isoformat()
                        rt["pending_reason"] = "unavailable"
                    elapsed = (dt_util.now() - datetime.fromisoformat(rt["pending_since"])).total_seconds()
                    remaining = max(0, rule.unavailable_delay - elapsed)
                    if remaining <= 0:
                        await self._trigger(rule, actual, "unavailable")
                    else:
                        self._schedule_timer(rule, remaining)
                elif current:
                    await self._maybe_repeat(rule, current)
                self._schedule_save()
                return

        if rt.get("pending_reason") == "unavailable":
            rt.pop("pending_since", None)
            rt.pop("pending_reason", None)
            self._cancel_timer(rule.id)

        last_raw = rt.get("last_heartbeat")
        if not last_raw:
            last_changed = getattr(state, "last_changed", None)
            last_raw = (last_changed or dt_util.now()).isoformat()
            rt["last_heartbeat"] = last_raw
        elapsed = max(0, (dt_util.now() - datetime.fromisoformat(last_raw)).total_seconds())
        remaining = max(0, rule.duration - elapsed)

        if remaining > 0:
            self._cancel_timer(rule.id)
            self._schedule_timer(rule, remaining)
            rt.pop("latched", None)
            if current:
                await self.async_resolve(current["id"], "heartbeat_restored")
        elif current:
            await self._maybe_repeat(rule, current)
            if rule.repeat and not current.get("acknowledged_at"):
                self._cancel_timer(rule.id)
                self._schedule_timer(rule, rule.repeat)
        elif not rt.get("latched"):
            await self._trigger(rule, actual, "heartbeat_timeout")
            if rule.repeat:
                self._schedule_timer(rule, rule.repeat)
        self._schedule_save()

    def _schedule_timer(self, rule: Rule, delay: float) -> None:
        if rule.id in self._timers:
            return
        @callback
        def due(_now) -> None:
            self._timers.pop(rule.id, None)
            self.hass.async_create_task(self.async_evaluate(rule, self.hass.states.get(rule.entity_id)))
        self._timers[rule.id] = async_call_later(self.hass, delay, due)

    def _cancel_timer(self, rule_id: str) -> None:
        cancel = self._timers.pop(rule_id, None)
        if cancel:
            cancel()

    async def _trigger(self, rule: Rule, actual: Any, reason: str) -> None:
        now = dt_util.now()
        rt = self.runtime.setdefault(rule.id, {})
        cooldown_until = rt.get("cooldown_until")
        if cooldown_until and datetime.fromisoformat(cooldown_until) > now:
            return
        alert = {
            "id": str(uuid4()), "rule_id": rule.id, "rule_name": rule.name,
            "entity_id": rule.entity_id, "severity": rule.severity, "value": actual,
            "kind": rule.kind, "reason": reason, "started_at": now.isoformat(), "acknowledged_at": None,
            "last_repeated_at": None,
        }
        self.alerts[alert["id"]] = alert
        rt["latched"] = True
        rt.pop("pending_since", None)
        rt.pop("pending_reason", None)
        if rule.cooldown:
            rt["cooldown_until"] = (now + timedelta(seconds=rule.cooldown)).isoformat()
        self._record("alert", alert)
        self.hass.bus.async_fire(EVENT_ALERT, dict(alert))
        if rule.kind == "fault":
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "notification_id": f"{DOMAIN}_fault_{rule.id}",
                    "title": f"Nodarion Pager: {rule.name}",
                    "message": f"{rule.entity_id}: {actual}",
                },
                blocking=False,
            )
        await self._async_forward_notification(alert, "alert")
        await self._async_save()

    async def _maybe_repeat(self, rule: Rule, alert: dict[str, Any]) -> None:
        await self._async_escalate(rule, alert)
        if not rule.repeat or alert.get("acknowledged_at"):
            return
        last = alert.get("last_repeated_at") or alert["started_at"]
        if (dt_util.now() - datetime.fromisoformat(last)).total_seconds() >= rule.repeat:
            alert["last_repeated_at"] = dt_util.now().isoformat()
            self._record("repeat", alert)
            self.hass.bus.async_fire(EVENT_ALERT, {**alert, "repeated": True})
            await self._async_forward_notification(alert, "repeat")

    async def _async_escalate(self, rule: Rule, alert: dict[str, Any]) -> None:
        elapsed = (dt_util.now() - datetime.fromisoformat(alert["started_at"])).total_seconds()
        sent = set(alert.setdefault("escalations_sent", []))
        for index, stage in enumerate(rule.escalation):
            key = str(index)
            if key in sent or elapsed < max(0, float(stage.get("after", 0))):
                continue
            escalated = {**alert, "severity": stage.get("severity", alert["severity"])}
            if isinstance(stage.get("notification_targets"), list):
                escalated["notification_targets"] = stage["notification_targets"]
            await self._async_forward_notification(escalated, "repeat")
            sent.add(key)
            alert["escalations_sent"] = sorted(sent)
            self._record("escalated", escalated)

    async def async_acknowledge(self, alert_id: str) -> None:
        alert = self.alerts.get(alert_id)
        if not alert or alert.get("acknowledged_at"):
            return
        alert["acknowledged_at"] = dt_util.now().isoformat()
        self._record("acknowledged", alert)
        self.hass.bus.async_fire(EVENT_ACKNOWLEDGED, dict(alert))
        await self._async_save()

    async def async_resolve(self, alert_id: str, reason: str = "manual") -> None:
        alert = self.alerts.pop(alert_id, None)
        if not alert:
            return
        rule = self.rules.get(alert["rule_id"])
        resolved_value = (
            self._value(rule, self.hass.states.get(rule.entity_id))
            if rule
            else alert.get("value")
        )
        alert = {
            **alert,
            "value": resolved_value,
            "resolved_at": dt_util.now().isoformat(),
            "resolve_reason": reason,
        }
        self._record("resolved", alert)
        self.hass.bus.async_fire(EVENT_RESOLVED, dict(alert))
        if alert.get("kind") == "fault" or (rule and rule.kind == "fault"):
            await self.hass.services.async_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": f"{DOMAIN}_fault_{alert['rule_id']}"},
                blocking=False,
            )
        await self._async_forward_notification(alert, "resolved")
        await self._async_save()

    async def async_save_rule(self, raw: dict[str, Any]) -> Rule:
        rule = Rule.from_dict(raw)
        self.rules[rule.id] = rule
        self._resubscribe()
        self._refresh_repairs()
        if self._startup_ready:
            await self.async_evaluate(rule, self.hass.states.get(rule.entity_id))
        await self._async_save()
        return rule

    async def async_delete_rule(self, rule_id: str) -> None:
        for alert in list(self.alerts.values()):
            if alert["rule_id"] == rule_id:
                await self.async_resolve(alert["id"], "rule_deleted")
        self.rules.pop(rule_id, None)
        ir.async_delete_issue(self.hass, DOMAIN, f"missing_entity_{rule_id}")
        ir.async_delete_issue(self.hass, DOMAIN, f"missing_target_{rule_id}")
        self.runtime.pop(rule_id, None)
        self._cancel_timer(rule_id)
        self._resubscribe()
        self._refresh_repairs()
        await self._async_save()

    async def async_toggle_rule(self, rule_id: str, enabled: bool) -> None:
        rule = self.rules[rule_id]
        rule.enabled = enabled
        if not enabled:
            self._cancel_timer(rule_id)
            self.runtime.pop(rule_id, None)
            for alert in list(self.alerts.values()):
                if alert["rule_id"] == rule_id:
                    await self.async_resolve(alert["id"], "rule_disabled")
        elif self._startup_ready:
            await self.async_evaluate(rule, self.hass.states.get(rule.entity_id))
        self._resubscribe()
        await self._async_save()

    async def async_pause_rule(self, rule_id: str, seconds: float) -> None:
        rule = self.rules[rule_id]
        rule.paused_until = (dt_util.now() + timedelta(seconds=max(0, seconds))).isoformat() if seconds else None
        self._cancel_timer(rule_id)
        await self._async_save()

    async def async_set_maintenance(self, seconds: float) -> None:
        self.settings["maintenance_until"] = (dt_util.now() + timedelta(seconds=max(0, seconds))).isoformat() if seconds else None
        if seconds:
            for cancel in self._timers.values():
                cancel()
            self._timers.clear()
        await self._async_save()

    def export_rules(self) -> list[dict[str, Any]]:
        return [rule.as_dict() for rule in self.rules.values()]

    async def async_import_rules(self, items: Any, replace: bool = False) -> None:
        if not isinstance(items, list):
            raise ValueError("rules must be a list")
        imported: dict[str, Rule] = {}
        for raw in items:
            rule = Rule.from_dict(raw)
            if rule.id in imported:
                raise ValueError("duplicate rule id")
            imported[rule.id] = rule
        if replace:
            for rule_id in list(self.rules):
                self._cancel_timer(rule_id)
            self.rules = imported
        else:
            for rule in imported.values():
                if rule.id in self.rules:
                    rule.id = str(uuid4())
                self.rules[rule.id] = rule
        self._resubscribe()
        await self._async_save()

    async def async_duplicate_rule(self, rule_id: str) -> Rule:
        raw = self.rules[rule_id].as_dict()
        raw.update({"id": str(uuid4()), "name": f"{raw['name']} (Kopie)", "enabled": False, "created_at": dt_util.now().isoformat(), "paused_until": None})
        return await self.async_save_rule(raw)

    async def async_comment(self, alert_id: str, comment: str, user_id: str | None) -> None:
        alert = self.alerts.get(alert_id)
        if not alert:
            raise ValueError("alert not found")
        item = {"comment": comment.strip()[:1000], "user_id": user_id, "timestamp": dt_util.now().isoformat()}
        alert.setdefault("comments", []).append(item)
        self._record("commented", {**alert, **item})
        await self._async_save()

    def _resubscribe(self) -> None:
        if self._unsub:
            self._unsub()
        ids = sorted({entity_id for rule in self.rules.values() if rule.enabled for entity_id in [rule.entity_id, *(str(item.get("entity_id")) for item in rule.conditions if item.get("entity_id"))]})
        self._unsub = async_track_state_change_event(self.hass, ids, self._state_changed) if ids else None

    def _active_for_rule(self, rule_id: str) -> dict[str, Any] | None:
        return next((a for a in self.alerts.values() if a["rule_id"] == rule_id), None)

    def _record(self, event: str, alert: dict[str, Any]) -> None:
        self.history.insert(0, {"event": event, "timestamp": dt_util.now().isoformat(), **alert})
        cutoff = dt_util.now() - timedelta(days=int(self.settings["history_days"]))
        self.history = [h for h in self.history if datetime.fromisoformat(h["timestamp"]) >= cutoff]
        self.history = self.history[: int(self.settings["history_limit"])]

    async def async_update_settings(self, settings: dict[str, Any]) -> None:
        self.settings["history_days"] = min(3650, max(1, int(settings.get("history_days", 30))))
        self.settings["history_limit"] = min(100000, max(100, int(settings.get("history_limit", 10000))))
        self.settings["startup_delay"] = min(600, max(0, int(settings.get("startup_delay", 60))))
        self.settings["notifications_enabled"] = bool(settings.get("notifications_enabled", False))
        profiles = settings.get("notification_target_profiles", {})
        available_ids = {item["id"] for item in self._notification_targets(apply_profiles=False)}
        cleaned_profiles: dict[str, dict[str, str]] = {}
        if isinstance(profiles, dict):
            for target_id, profile in profiles.items():
                if target_id not in available_ids or not isinstance(profile, dict):
                    continue
                name = str(profile.get("name", "")).strip()[:80]
                color = str(profile.get("color", "")).strip().lower()
                if len(color) != 7 or not color.startswith("#") or any(char not in "0123456789abcdef" for char in color[1:]):
                    color = "#d7ad52"
                cleaned_profiles[target_id] = {"name": name, "color": color}
        self.settings["notification_target_profiles"] = cleaned_profiles
        requested = settings.get("notification_targets", [])
        available = {item["id"] for item in self._notification_targets()}
        self.settings["notification_targets"] = [
            target for target in requested if isinstance(target, str) and target in available
        ]
        for key in ("notify_info", "notify_warning", "notify_critical", "notify_resolved"):
            self.settings[key] = bool(settings.get(key, self.settings.get(key, False)))
        await self._async_save()

    def _notification_targets(self, apply_profiles: bool = True) -> list[dict[str, str]]:
        """Return modern notify entities and legacy notifier actions."""
        targets: list[dict[str, str]] = []
        for state in self.hass.states.async_all("notify"):
            targets.append({
                "id": f"entity:{state.entity_id}",
                "name": state.name or state.entity_id,
                "type": "entity",
                "detail": state.entity_id,
            })
        services = self.hass.services.async_services().get("notify", {})
        for service in sorted(services):
            if service == "send_message":
                continue
            targets.append({
                "id": f"service:notify.{service}",
                "name": service.replace("_", " ").title(),
                "type": "service",
                "detail": f"notify.{service}",
            })
        if apply_profiles:
            profiles = self.settings.get("notification_target_profiles", {})
            for target in targets:
                profile = profiles.get(target["id"], {}) if isinstance(profiles, dict) else {}
                target["original_name"] = target["name"]
                target["name"] = str(profile.get("name") or target["name"])
                target["color"] = str(profile.get("color") or "#d7ad52")
        return targets

    async def async_test_notification_target(self, target: str) -> None:
        """Send a test message to exactly one configured Home Assistant target."""
        available = {item["id"] for item in self._notification_targets()}
        if target not in available:
            raise ValueError("Benachrichtigungsziel ist nicht mehr verfügbar")
        title = "Nodarion Pager · Test"
        message = "Testbenachrichtigung erfolgreich empfangen."
        try:
            if target.startswith("entity:"):
                await self.hass.services.async_call(
                    "notify", "send_message", {"message": f"{title}\n{message}"},
                    target={"entity_id": target.removeprefix("entity:")}, blocking=True,
                )
            else:
                domain_service = target.removeprefix("service:")
                domain, service = domain_service.split(".", 1)
                await self.hass.services.async_call(
                    domain, service, {"title": title, "message": message}, blocking=True,
                )
        except Exception as err:
            _LOGGER.exception("Could not send Pager test notification to %s", target)
            raise ValueError(f"Testbenachrichtigung fehlgeschlagen: {err}") from err

    async def _async_forward_notification(self, alert: dict[str, Any], event: str) -> None:
        """Forward without ever interrupting monitoring when one target fails."""
        if not self.settings.get("notifications_enabled"):
            return
        if event == "resolved":
            if not self.settings.get("notify_resolved"):
                return
            title = f"Nodarion Pager · OK · {alert['rule_name']}"
            message = f"Entwarnung: {alert['entity_id']} ist wieder im Normalzustand."
        else:
            if not self.settings.get(f"notify_{alert.get('severity', 'warning')}", False):
                return
            repeated = " · Wiederholung" if event == "repeat" else ""
            title = f"Nodarion Pager · {str(alert.get('severity', 'warning')).upper()}{repeated}"
            message = f"{alert['rule_name']}\n{alert['entity_id']}: {alert.get('value', '–')}"
        available = {item["id"] for item in self._notification_targets()}
        global_targets = self.settings.get("notification_targets", [])
        rule = self.rules.get(str(alert.get("rule_id", "")))
        rule_targets = alert.get("notification_targets") if "notification_targets" in alert else (rule.notification_targets if rule else None)
        selected_targets = [] if rule_targets is None else rule_targets
        for target in selected_targets:
            if target not in global_targets:
                continue
            if target not in available:
                continue
            try:
                if target.startswith("entity:"):
                    # Modern notify entities accept `message`, but no separate
                    # `title`. Keep the heading by placing it in the message.
                    await self.hass.services.async_call(
                        "notify", "send_message", {"message": f"{title}\n{message}"},
                        target={"entity_id": target.removeprefix("entity:")}, blocking=False,
                    )
                else:
                    domain_service = target.removeprefix("service:")
                    domain, service = domain_service.split(".", 1)
                    await self.hass.services.async_call(
                        domain, service, {"title": title, "message": message}, blocking=False,
                    )
            except Exception:  # A notifier must never stop the rule engine.
                self.last_notification_errors[target] = dt_util.now().isoformat()
                _LOGGER.exception("Could not forward Pager notification to %s", target)

    def frontend_state(self, scope: str = "full", offset: int = 0, limit: int = 100) -> dict[str, Any]:
        base = {
            "version": VERSION, "rules": [r.as_dict() for r in self.rules.values()],
            "alerts": sorted(self.alerts.values(), key=lambda a: a["started_at"], reverse=True),
            "runtime": self.runtime, "settings": self.settings,
        }
        if scope == "runtime":
            return base
        common_states = {
            "binary_sensor": ["on", "off"], "switch": ["on", "off"],
            "input_boolean": ["on", "off"], "light": ["on", "off"],
            "lock": ["locked", "unlocked", "locking", "unlocking", "jammed"],
            "cover": ["open", "closed", "opening", "closing"],
            "alarm_control_panel": ["disarmed", "armed_home", "armed_away", "armed_night", "armed_vacation", "triggered", "pending"],
            "person": ["home", "not_home"], "device_tracker": ["home", "not_home"],
        }
        entities = []
        for state in self.hass.states.async_all():
            domain = state.entity_id.split(".", 1)[0]
            attributes = state.attributes
            states = list(common_states.get(domain, []))
            for key in ("options", "hvac_modes", "preset_modes", "fan_modes", "swing_modes", "source_list", "effect_list"):
                values = attributes.get(key)
                if isinstance(values, (list, tuple)):
                    states.extend(str(value) for value in values)
            if state.state not in {"unknown", "unavailable", ""}:
                states.append(state.state)
            states = list(dict.fromkeys(states))
            try:
                float(state.state)
                numeric = domain not in common_states
            except (TypeError, ValueError):
                numeric = bool(attributes.get("unit_of_measurement")) and not states[:-1]
            entities.append({
                "entity_id": state.entity_id, "name": state.name or state.entity_id,
                "state": state.state, "value_type": "analog" if numeric else "digital",
                "states": states, "unit": attributes.get("unit_of_measurement"),
                "device_class": attributes.get("device_class"),
            })
        base.update({
            "history": self.history[offset:offset + limit], "history_total": len(self.history),
            "notification_targets": self._notification_targets(),
            "entities": sorted(entities, key=lambda e: e["name"].casefold()),
            "diagnostics": self.diagnostics(),
        })
        return base

    def diagnostics(self) -> dict[str, Any]:
        missing_entities = sorted(rule.entity_id for rule in self.rules.values() if self.hass.states.get(rule.entity_id) is None)
        available_targets = {item["id"] for item in self._notification_targets()}
        missing_targets = sorted({target for rule in self.rules.values() for target in (rule.notification_targets or []) if target not in available_targets})
        return {
            "version": VERSION, "rules": len(self.rules), "active_alerts": len(self.alerts),
            "pending": sum(bool(item.get("pending_since")) for item in self.runtime.values()),
            "timers": len(self._timers), "missing_entities": missing_entities,
            "missing_notification_targets": missing_targets,
            "last_notification_errors": self.last_notification_errors,
        }

    def _refresh_repairs(self) -> None:
        """Expose broken rule references in Home Assistant Repairs."""
        available_targets = {item["id"] for item in self._notification_targets()}
        for rule in self.rules.values():
            issue_id = f"missing_entity_{rule.id}"
            if self.hass.states.get(rule.entity_id) is None:
                ir.async_create_issue(
                    self.hass, DOMAIN, issue_id, is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="missing_entity",
                    translation_placeholders={"entity_id": rule.entity_id, "rule_name": rule.name},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
            target_issue_id = f"missing_target_{rule.id}"
            missing = [target for target in (rule.notification_targets or []) if target not in available_targets]
            if missing:
                ir.async_create_issue(
                    self.hass, DOMAIN, target_issue_id, is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="missing_target",
                    translation_placeholders={"target": missing[0], "rule_name": rule.name},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, target_issue_id)

    def _schedule_save(self) -> None:
        self._save_dirty = True
        if not self._save_task or self._save_task.done():
            self._save_task = self.hass.async_create_task(self._async_save_loop())

    async def _async_save_loop(self) -> None:
        while self._save_dirty:
            self._save_dirty = False
            await self._async_save()

    async def _async_save(self) -> None:
        await self.store.async_save({
            "schema_version": 2,
            "rules": [r.as_dict() for r in self.rules.values()], "alerts": list(self.alerts.values()),
            "history": self.history, "runtime": self.runtime, "settings": self.settings,
        })
        async_dispatcher_send(self.hass, SIGNAL_UPDATE, self.frontend_state(scope="runtime"))
