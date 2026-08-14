"""Data models and comparison helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .const import OPERATORS, RESET_MODES, RULE_KINDS, SEVERITIES, UNAVAILABLE_BEHAVIORS


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
