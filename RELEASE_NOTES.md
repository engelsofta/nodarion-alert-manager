# Nodarion Pager 1.0.0

## Your home has a lot to say. Nodarion knows when it should beep.

Version 1.0 turns Nodarion into both a local alert center and a Live Activity engine for Home Assistant.

### Live Activities are here

Put running processes on the Lock Screen and Dynamic Island without turning them into alarms. Washing machines, robotic mowers, charging sessions, deliveries and other entity-driven processes can now show:

- independent start and end conditions;
- dynamic status text;
- progress and remaining time;
- an on-device countdown;
- custom icons, colors and tap destinations;
- selected Companion App devices;
- reliable throttling, restoration and cleanup.

The new spacious three-step wizard includes searchable entity selection, a phone-style preview and a safe ten-second test.

### A serious pager—without taking itself too seriously

Nodarion combines threshold, digital, fault and heartbeat rules with delays, hysteresis, cooldowns, schedules, maintenance windows, acknowledgement, repetition and escalation. Alerts explain exactly why they fired, while history, comments, charts, diagnostics and Repairs keep operation traceable.

### Privacy by design

Nodarion has no cloud account, analytics or telemetry. Evaluation and storage stay inside Home Assistant; only explicitly selected notification targets receive data.

### Requirements

- Home Assistant 2026.7.0 or later
- Live Activities additionally require a compatible Companion App/device and a `notify.mobile_app_*` service

See the [README](https://github.com/engelsofta/nodarion-alert-manager#readme) and [full changelog](https://github.com/engelsofta/nodarion-alert-manager/blob/main/CHANGELOG.md) for details.
