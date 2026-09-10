"""Data models and comparison helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .const import OPERATORS, RESET_MODES, RULE_KINDS, SEVERITIES, UNAVAILABLE_BEHAVIORS


def _conditions(data: Any, field_name: str) -> list[dict[str, Any]]:
    items = [dict(item) for item in data or [] if isinstance(item, dict)]
    if not items:
        raise ValueError(f"{field_name} requires at least one condition")
    for item in items:
        if not item.get("entity_id") or "." not in str(item["entity_id"]):
            raise ValueError(f"invalid {field_name} entity")
        if item.get("operator", "eq") not in OPERATORS:
            raise ValueError(f"invalid {field_name} operator")
        if item.get("value") in (None, ""):
            raise ValueError(f"invalid {field_name} value")
    return items


@dataclass(slots=True)
class Rule:
    """One entity monitoring rule."""

    id: str
    name: str
    entity_id: str
    operator: str
    kind: str = "threshold"
    value: Any = None
    value_upper: Any = None
    attribute: str | None = None
    duration: float = 0
    severity: str = "warning"
    unavailable_behavior: str = "alert"
    unavailable_delay: float = 60
    reset_mode: str = "automatic"
    hysteresis: float = 0
    cooldown: float = 0
    repeat: float = 0
    notification_targets: list[str] | None = None
    conditions: list[dict[str, Any]] = field(default_factory=list)
    condition_mode: str = "and"
    schedule: dict[str, Any] = field(default_factory=dict)
    escalation: list[dict[str, Any]] = field(default_factory=list)
    paused_until: str | None = None
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        rule = cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name") or "New rule").strip(),
            entity_id=str(data.get("entity_id") or "").strip(),
            operator=str(data.get("operator") or "eq"),
            kind=str(data.get("kind") or "threshold"),
            value=data.get("value"),
            value_upper=data.get("value_upper"),
            attribute=(str(data["attribute"]).strip() if data.get("attribute") else None),
            duration=max(0, float(data.get("duration") or 0)),
            severity=str(data.get("severity") or "warning"),
            unavailable_behavior=str(data.get("unavailable_behavior") or "alert"),
            unavailable_delay=max(0, float(data.get("unavailable_delay", 60) or 0)),
            reset_mode=str(data.get("reset_mode") or "automatic"),
            hysteresis=max(0, float(data.get("hysteresis") or 0)),
            cooldown=max(0, float(data.get("cooldown") or 0)),
            repeat=max(0, float(data.get("repeat") or 0)),
            notification_targets=(
                [str(target) for target in data["notification_targets"] if isinstance(target, str)]
                if isinstance(data.get("notification_targets"), list)
                else None
            ),
            conditions=[item for item in data.get("conditions", []) if isinstance(item, dict)],
            condition_mode=str(data.get("condition_mode") or "and"),
            schedule=dict(data.get("schedule") or {}),
            escalation=[item for item in data.get("escalation", []) if isinstance(item, dict)],
            paused_until=str(data["paused_until"]) if data.get("paused_until") else None,
            enabled=bool(data.get("enabled", True)),
            created_at=str(data.get("created_at") or datetime.now().astimezone().isoformat()),
        )
        rule.validate()
        return rule

    def validate(self) -> None:
        if not self.name or not self.entity_id or "." not in self.entity_id:
            raise ValueError("name and entity_id are required")
        if self.operator not in OPERATORS:
            raise ValueError("invalid operator")
        if self.kind not in RULE_KINDS:
            raise ValueError("invalid rule kind")
        if self.kind == "heartbeat" and self.duration <= 0:
            raise ValueError("heartbeat timeout must be greater than zero")
        if self.severity not in SEVERITIES:
            raise ValueError("invalid severity")
        if self.unavailable_behavior not in UNAVAILABLE_BEHAVIORS:
            raise ValueError("invalid unavailable behavior")
        if self.reset_mode not in RESET_MODES:
            raise ValueError("invalid reset mode")
        if self.condition_mode not in {"and", "or"}:
            raise ValueError("invalid condition mode")
        if self.operator in {"between", "outside"} and self.value_upper in (None, ""):
            raise ValueError("upper value required")
        if self.kind != "heartbeat" and self.value in (None, ""):
            raise ValueError("value required")
        for condition in self.conditions:
            if not condition.get("entity_id") or condition.get("operator", "eq") not in OPERATORS:
                raise ValueError("invalid additional condition")
        weekdays = self.schedule.get("weekdays")
        if weekdays is not None and (not isinstance(weekdays, list) or any(day not in range(7) for day in weekdays)):
            raise ValueError("invalid schedule weekdays")
        for stage in self.escalation:
            if float(stage.get("after", 0)) < 0 or stage.get("severity", self.severity) not in SEVERITIES:
                raise ValueError("invalid escalation")
        if self.paused_until:
            datetime.fromisoformat(self.paused_until)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LiveActivity:
    """A non-alarm process shown by the Home Assistant companion app."""

    id: str
    name: str
    start_conditions: list[dict[str, Any]]
    end_conditions: list[dict[str, Any]]
    title: str
    message_template: str
    critical_text_template: str | None = None
    condition_mode: str = "and"
    end_condition_mode: str = "or"
    progress_entity: str | None = None
    progress_attribute: str | None = None
    progress_max: float = 100
    progress_bar_direction: str = "increasing"
    remaining_time_entity: str | None = None
    remaining_time_attribute: str | None = None
    remaining_time_unit: str = "minutes"
    icon: str = "mdi:progress-clock"
    color: str = "#2196f3"
    url: str | None = None
    notification_targets: list[str] = field(default_factory=list)
    update_entities: list[str] = field(default_factory=list)
    minimum_update_interval: float = 30
    maximum_runtime: float = 0
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LiveActivity:
        item = cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name") or "New live activity").strip(),
            start_conditions=_conditions(data.get("start_conditions"), "start_conditions"),
            end_conditions=_conditions(data.get("end_conditions"), "end_conditions"),
            title=str(data.get("title") or data.get("name") or "Live Activity").strip(),
            message_template=str(data.get("message_template") or "{name}").strip(),
            critical_text_template=(str(data["critical_text_template"]).strip() if data.get("critical_text_template") else None),
            condition_mode=str(data.get("condition_mode") or "and"),
            end_condition_mode=str(data.get("end_condition_mode") or "or"),
            progress_entity=(str(data["progress_entity"]).strip() if data.get("progress_entity") else None),
            progress_attribute=(str(data["progress_attribute"]).strip() if data.get("progress_attribute") else None),
            progress_max=max(0.000001, float(data.get("progress_max") or 100)),
            progress_bar_direction=str(data.get("progress_bar_direction") or "increasing"),
            remaining_time_entity=(str(data["remaining_time_entity"]).strip() if data.get("remaining_time_entity") else None),
            remaining_time_attribute=(str(data["remaining_time_attribute"]).strip() if data.get("remaining_time_attribute") else None),
            remaining_time_unit=str(data.get("remaining_time_unit") or "minutes"),
            icon=str(data.get("icon") or "mdi:progress-clock").strip(),
            color=str(data.get("color") or "#2196f3").strip().lower(),
            url=(str(data["url"]).strip() if data.get("url") else None),
            notification_targets=[str(value) for value in data.get("notification_targets", []) if isinstance(value, str)],
            update_entities=[str(value).strip() for value in data.get("update_entities", []) if isinstance(value, str) and "." in value],
            minimum_update_interval=max(0, float(data.get("minimum_update_interval") or 0)),
            maximum_runtime=max(0, float(data.get("maximum_runtime") or 0)),
            enabled=bool(data.get("enabled", True)),
            created_at=str(data.get("created_at") or datetime.now().astimezone().isoformat()),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if not self.name or not self.title or not self.message_template:
            raise ValueError("name, title and message are required")
        if self.condition_mode not in {"and", "or"} or self.end_condition_mode not in {"and", "or"}:
            raise ValueError("invalid condition mode")
        if self.progress_bar_direction not in {"increasing", "decreasing"}:
            raise ValueError("invalid progress bar direction")
        if self.remaining_time_unit not in {"seconds", "minutes", "timestamp"}:
            raise ValueError("invalid remaining time unit")
        if len(self.color) != 7 or not self.color.startswith("#") or any(char not in "0123456789abcdef" for char in self.color[1:]):
            raise ValueError("color must be a hex value")
        for entity_id in (self.progress_entity, self.remaining_time_entity):
            if entity_id and "." not in entity_id:
                raise ValueError("invalid display entity")

    def watched_entities(self) -> set[str]:
        entities = {
            *[str(item["entity_id"]) for item in self.start_conditions],
            *[str(item["entity_id"]) for item in self.end_conditions],
            *([self.progress_entity] if self.progress_entity else []),
            *([self.remaining_time_entity] if self.remaining_time_entity else []),
            *self.update_entities,
        }
        for template in (self.title, self.message_template, self.critical_text_template or ""):
            entities.update(token for token in re.findall(r"\{([^{}]+)\}", template) if "." in token)
        return entities

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def coerce_pair(actual: Any, expected: Any) -> tuple[Any, Any]:
    """Prefer numerical comparison, fall back to normalized strings."""
    try:
        return float(actual), float(expected)
    except (TypeError, ValueError):
        return str(actual).casefold(), str(expected).casefold()


def matches(rule: Rule, actual: Any, *, resetting: bool = False) -> bool:
    """Return whether a value violates a rule."""
    left, right = coerce_pair(actual, rule.value)
    upper = coerce_pair(actual, rule.value_upper)[1] if rule.value_upper is not None else None
    h = rule.hysteresis if resetting and isinstance(left, float) else 0
    if rule.operator == "eq":
        return left == right
    if rule.operator == "ne":
        return left != right
    if rule.operator == "gt":
        return left > right - h
    if rule.operator == "gte":
        return left >= right - h
    if rule.operator == "lt":
        return left < right + h
    if rule.operator == "lte":
        return left <= right + h
    if rule.operator == "between":
        return right - h <= left <= upper + h
    if rule.operator == "outside":
        return left < right + h or left > upper - h
    return False


def matches_condition(condition: dict[str, Any], actual: Any) -> bool:
    """Evaluate an additional condition using the normal comparison semantics."""
    probe = Rule.from_dict({
        "name": "condition", "entity_id": str(condition.get("entity_id") or "sensor.invalid"),
        "operator": condition.get("operator", "eq"), "value": condition.get("value"),
        "value_upper": condition.get("value_upper"),
    })
    return matches(probe, actual)
