"""Constants for Nodarion Pager."""

DOMAIN = "nodarion_pager"
NAME = "Engelsoft Nodarion Pager"
VERSION = "0.7.7"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.state"
PANEL_URL = "nodarion-pager"
PANEL_TITLE = "Engelsoft Pager"
STATIC_URL = "/nodarion_pager_static"
SIGNAL_UPDATE = f"{DOMAIN}_update"
EVENT_ALERT = "nodarion_pager_alert"
EVENT_RESOLVED = "nodarion_pager_resolved"
EVENT_ACKNOWLEDGED = "nodarion_pager_acknowledged"

DEFAULT_SETTINGS = {
    "history_days": 30,
    "history_limit": 10000,
    "startup_delay": 60,
    "default_unavailable_behavior": "alert",
    "notifications_enabled": False,
    "notification_targets": [],
    "notification_target_profiles": {},
    "notify_info": False,
    "notify_warning": True,
    "notify_critical": True,
    "notify_resolved": True,
    "maintenance_until": None,
}

OPERATORS = {"eq", "ne", "gt", "lt", "gte", "lte", "between", "outside"}
UNAVAILABLE_BEHAVIORS = {"ignore", "pause", "alert"}
SEVERITIES = {"info", "warning", "critical"}
RESET_MODES = {"automatic", "manual"}
RULE_KINDS = {"threshold", "binary", "fault", "heartbeat"}
