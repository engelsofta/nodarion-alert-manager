# Nodarion Pager for Home Assistant

<div align="center">
  <img src="custom_components/nodarion_pager/brand/logo.svg" alt="Nodarion Pager" width="420">

  ### Your home has a lot to say. Nodarion knows when it should beep.
  ### Dein Zuhause hat viel zu sagen. Nodarion weiß, wann es piepen muss.

  A local alert center **and** Live Activity engine for Home Assistant.

  [![Release](https://img.shields.io/github/v/release/engelsofta/nodarion-alert-manager?style=flat-square)](https://github.com/engelsofta/nodarion-alert-manager/releases/latest)
  [![Validation](https://img.shields.io/github/actions/workflow/status/engelsofta/nodarion-alert-manager/validate.yml?branch=main&style=flat-square&label=validation)](https://github.com/engelsofta/nodarion-alert-manager/actions/workflows/validate.yml)
  [![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square&logo=homeassistantcommunitystore)](https://www.hacs.xyz/)
  [![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.7%2B-18BCF2?style=flat-square&logo=homeassistant)](https://www.home-assistant.io/)
  [![ZIP downloads](https://img.shields.io/github/downloads/engelsofta/nodarion-alert-manager/latest/nodarion-alert-manager.zip?style=flat-square&label=ZIP%20downloads&color=blue)](https://github.com/engelsofta/nodarion-alert-manager/releases/latest/download/nodarion-alert-manager.zip)
  [![License](https://img.shields.io/github/license/engelsofta/nodarion-alert-manager?style=flat-square)](LICENSE)

  [English](#english) · [Deutsch](#deutsch)
</div>

---

## English

Nodarion Pager turns Home Assistant entities into an operations-ready monitoring center. It detects abnormal states, suppresses short-lived noise, routes actionable alerts and keeps a traceable history. Its independent **Live Activity engine** also puts normal running processes—washing, mowing, charging or deliveries—directly on a compatible phone's Lock Screen and Dynamic Island.

Everything is configured from a responsive Home Assistant panel and evaluated locally.

### Why Nodarion?

| Capability | Benefit |
| --- | --- |
| Central alarm dashboard | One calm view for active, pending and acknowledged alerts |
| Four rule types | Monitor numeric thresholds, digital states, faults and missing heartbeats |
| Noise control | Delay, hysteresis and cooldown prevent alerts from brief spikes |
| Operational controls | Maintenance windows, schedules and rule pauses avoid expected downtime noise |
| Escalation | Repeat or raise severity while an alert remains unresolved |
| Notification routing | Choose recipients per rule and escalation stage |
| Explainable alerts | See the current value and exact condition that caused an alert |
| Traceability | History, comments, Recorder charts and privacy-conscious diagnostics |
| Local processing | No Nodarion cloud, tracking or telemetry |

### Live Activities: running information that stays in sight

> The washing machine is running—and now the information runs with it.

Live Activities are independent from alarm rules. They are designed for useful, non-fault states such as:

- a washing machine or dryer with phase, progress and remaining time;
- a robotic mower currently mowing, returning or charging;
- an EV charging session with battery percentage;
- a dishwasher, oven, 3D printer or long-running Home Assistant script;
- a delivery or any process represented by Home Assistant entities.

Every Live Activity supports:

- independent start and end conditions;
- searchable entity selection by name or entity ID;
- dynamic `{entity.id}` placeholders in title and text;
- an optional progress entity and configurable maximum;
- remaining time in seconds, minutes or as an end timestamp;
- an on-device countdown without minute-by-minute push traffic;
- icon, color and a Home Assistant tap destination;
- per-device delivery to `notify.mobile_app_*` services;
- update throttling and an optional maximum runtime;
- restoration after a Home Assistant restart;
- cleanup when the process ends, is disabled or deleted;
- a safe test activity that closes itself after ten seconds.

Live Activities appear on the iOS Lock Screen and Dynamic Island. Android Live Updates appear in supported system surfaces. Support requires Home Assistant 2026.7.0 or later, a compatible Companion App/device and a working connection between the device and Home Assistant.

### Screenshots

![Nodarion overview with anonymized demo data](docs/images/nodarion-overview.png)

![Nodarion rule list with anonymized demo data](docs/images/nodarion-rules.png)

### Install with HACS

1. Open **HACS → Integrations**.
2. Open the top-right menu and select **Custom repositories**.
3. Add `https://github.com/engelsofta/nodarion-alert-manager` as an **Integration**.
4. Install **Nodarion Pager** and restart Home Assistant.
5. Open **Settings → Devices & services → Add integration**.
6. Search for **Nodarion Pager** and complete setup.
7. Open **Nodarion Pager** from the sidebar.

[![Add HACS repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=engelsofta&repository=nodarion-alert-manager&category=integration)

### Manual installation

1. Download [`nodarion-alert-manager.zip`](https://github.com/engelsofta/nodarion-alert-manager/releases/latest/download/nodarion-alert-manager.zip).
2. Extract it to `/config/custom_components/nodarion_pager/`.
3. Restart Home Assistant.
4. Add **Nodarion Pager** from **Settings → Devices & services**.

Minimum supported version: **Home Assistant 2026.7.0**.

### Alert rules

| Type | Use case |
| --- | --- |
| Threshold | Numeric `=`, `≠`, `>`, `<`, `≥`, `≤`, between and outside comparisons |
| Digital / I/O | States such as `on`, `off`, `open`, `closed`, `1` or `0` |
| Fault | A state rule plus a visible persistent Home Assistant fault notification |
| Heartbeat | Alert when an entity stops changing for a configured period |

Rules can add further entity conditions using AND/OR logic, schedules, delayed unavailable handling, automatic or manual reset, escalation stages and selected notification recipients.

### Actions

| Action | Purpose |
| --- | --- |
| `nodarion_pager.acknowledge` | Mark an active alert as acknowledged and stop repeats |
| `nodarion_pager.resolve` | Resolve an active alert manually |
| `nodarion_pager.enable_rule` | Enable a rule by ID |
| `nodarion_pager.disable_rule` | Disable a rule and resolve its active alerts |
| `nodarion_pager.pause_rule` | Pause a rule for a number of seconds |
| `nodarion_pager.maintenance` | Start or stop a global maintenance window |

The required IDs are included in exported rule data and event payloads. Most day-to-day operations are easier from the Nodarion panel.

### Events, conditions and updates

| Event | Meaning |
| --- | --- |
| `nodarion_pager_alert` | A rule triggered or repeated |
| `nodarion_pager_resolved` | An alert was resolved |
| `nodarion_pager_acknowledged` | An alert was acknowledged |

These events can be used as Home Assistant automation triggers. Nodarion does not add custom automation condition types; its rule conditions are configured in the panel.

Nodarion listens to Home Assistant state-change events instead of polling devices. A one-minute housekeeping cycle handles schedules, timeouts, repeats, escalation and long-running Live Activities. Configuration, runtime state and history use Home Assistant's local storage helper.

### Known limitations

- Live Activities require a legacy-style `notify.mobile_app_*` service because the complete structured payload is needed.
- The Companion App and operating system control final presentation and delivery timing.
- iOS can throttle excessive remote updates and limits activity lifetime; Nodarion throttles updates and periodically refreshes long-running activities.
- Nodarion monitors existing Home Assistant entities; it does not communicate with appliances directly.

### Troubleshooting

- Restart Home Assistant and clear the browser cache after updating.
- Confirm selected entities and notification services still exist.
- For Live Activities, verify Companion App permissions, connectivity and Home Assistant 2026.7.0 or later.
- Check **Settings → System → Repairs** for missing references.
- Download integration diagnostics when reporting an issue; sensitive values are redacted automatically.

### Removal

1. Delete **Nodarion Pager** from **Settings → Devices & services**.
2. Remove `custom_components/nodarion_pager/` or uninstall it through HACS.
3. Restart Home Assistant.

Finish active Live Activities before uninstalling so their final clear command can reach the Companion App.

### Privacy and security

Rule evaluation, configuration and history stay inside Home Assistant. Nodarion has no external API, cloud account, analytics or telemetry. Data leaves Home Assistant only through notification targets explicitly selected by an administrator. Diagnostics redact entity IDs, names, values, comments and user IDs. Report security issues privately through the [security advisory form](https://github.com/engelsofta/nodarion-alert-manager/security/advisories/new).

---

## Deutsch

Nodarion Pager macht aus Home-Assistant-Entitäten eine betriebstaugliche Überwachungs- und Alarmzentrale. Die Integration erkennt ungewöhnliche Zustände, filtert kurze Störungen heraus, leitet Alarme gezielt weiter und führt eine nachvollziehbare Historie. Die unabhängige **Live-Activity-Engine** bringt zusätzlich ganz normale laufende Vorgänge—Waschen, Mähen, Laden oder Lieferungen—direkt auf Sperrbildschirm und Dynamic Island kompatibler Smartphones.

Alles wird über eine responsive Home-Assistant-Oberfläche eingerichtet und lokal ausgewertet.

### Warum Nodarion?

| Funktion | Vorteil |
| --- | --- |
| Zentrale Alarmübersicht | Aktive, ausstehende und quittierte Meldungen in einer ruhigen Ansicht |
| Vier Regeltypen | Grenzwerte, digitale Zustände, Störungen und fehlende Heartbeats überwachen |
| Schutz vor Fehlalarmen | Verzögerung, Hysterese und Cooldown filtern kurze Ausreißer |
| Betriebsgerechte Steuerung | Wartungsfenster, Zeitpläne und Regelpausen berücksichtigen geplante Stillstände |
| Eskalation | Wiederholen oder Priorität erhöhen, solange ein Problem ungelöst bleibt |
| Gezielte Weiterleitung | Empfänger pro Regel und Eskalationsstufe auswählen |
| Verständliche Alarme | Aktuellen Wert und konkrete Auslösebedingung direkt sehen |
| Nachvollziehbarkeit | Historie, Kommentare, Recorder-Diagramme und datensparsame Diagnosen |
| Lokale Verarbeitung | Keine Nodarion-Cloud, kein Tracking und keine Telemetrie |

### Live Activities: laufende Informationen, die im Blick bleiben

> Die Waschmaschine läuft. Die Information läuft einfach mit.

Live Activities sind unabhängig von Alarmregeln. Sie eignen sich unter anderem für Waschmaschinen, Trockner, Mähroboter, Elektroautos, Geschirrspüler, Backöfen, 3D-Drucker, Lieferungen und lange Home-Assistant-Skripte.

Jede Live Activity unterstützt:

- getrennte Start- und Endbedingungen;
- durchsuchbare Entitätsauswahl nach Name oder Entity-ID;
- dynamische `{entity.id}`-Platzhalter in Titel und Text;
- eine optionale Fortschrittsentität mit frei wählbarem Maximum;
- Restlaufzeit in Sekunden, Minuten oder als Endzeitpunkt;
- einen auf dem Smartphone laufenden Countdown ohne minütliche Push-Flut;
- Symbol, Farbe und Home-Assistant-Ziel beim Antippen;
- Auswahl einzelner `notify.mobile_app_*`-Geräte;
- Drosselung von Aktualisierungen und eine optionale maximale Laufzeit;
- Wiederherstellung nach einem Home-Assistant-Neustart;
- automatisches Schließen bei Ende, Deaktivierung oder Löschen;
- eine sichere Test-Activity, die sich nach zehn Sekunden selbst beendet.

Unter iOS erscheinen Live Activities auf Sperrbildschirm und Dynamic Island. Android Live Updates werden auf unterstützten Systemflächen angezeigt. Benötigt werden Home Assistant 2026.7.0 oder neuer, ein kompatibles Gerät mit Companion App und eine funktionierende Verbindung zu Home Assistant.

### Screenshots

![Nodarion Übersicht mit anonymisierten Demo-Daten](docs/images/nodarion-overview.png)

![Nodarion Regelliste mit anonymisierten Demo-Daten](docs/images/nodarion-rules.png)

### Installation über HACS

1. Öffne **HACS → Integrationen**.
2. Wähle oben rechts **Benutzerdefinierte Repositories**.
3. Füge `https://github.com/engelsofta/nodarion-alert-manager` als **Integration** hinzu.
4. Installiere **Nodarion Pager** und starte Home Assistant neu.
5. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
6. Suche nach **Nodarion Pager** und schließe die Einrichtung ab.
7. Öffne **Nodarion Pager** über die Seitenleiste.

[![HACS-Repository hinzufügen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=engelsofta&repository=nodarion-alert-manager&category=integration)

### Manuelle Installation

1. Lade [`nodarion-alert-manager.zip`](https://github.com/engelsofta/nodarion-alert-manager/releases/latest/download/nodarion-alert-manager.zip) herunter.
2. Entpacke den Inhalt nach `/config/custom_components/nodarion_pager/`.
3. Starte Home Assistant neu.
4. Füge **Nodarion Pager** unter **Einstellungen → Geräte & Dienste** hinzu.

Mindestversion: **Home Assistant 2026.7.0**.

### Alarmregeln

| Typ | Einsatz |
| --- | --- |
| Grenzwert | Numerische Vergleiche mit `=`, `≠`, `>`, `<`, `≥`, `≤`, innerhalb und außerhalb |
| Digital / I/O | Zustände wie `on`, `off`, `open`, `closed`, `1` oder `0` |
| Störung | Zustandsregel plus sichtbarer persistenter Home-Assistant-Störungsmeldung |
| Heartbeat | Alarm, wenn sich eine Entität über einen festgelegten Zeitraum nicht mehr ändert |

Regeln unterstützen zusätzliche Entitätsbedingungen mit UND/ODER, Zeitpläne, verzögerte Behandlung nicht verfügbarer Entitäten, automatische oder manuelle Rücksetzung, Eskalationsstufen und ausgewählte Empfänger.

### Aktionen

| Aktion | Zweck |
| --- | --- |
| `nodarion_pager.acknowledge` | Aktiven Alarm quittieren und Wiederholungen stoppen |
| `nodarion_pager.resolve` | Aktiven Alarm manuell auflösen |
| `nodarion_pager.enable_rule` | Regel über ihre ID aktivieren |
| `nodarion_pager.disable_rule` | Regel deaktivieren und aktive Alarme auflösen |
| `nodarion_pager.pause_rule` | Regel für eine Anzahl Sekunden pausieren |
| `nodarion_pager.maintenance` | Globales Wartungsfenster starten oder beenden |

Die benötigten IDs stehen im Regelexport und in Ereignisdaten. Im Alltag ist die Bedienung über die Nodarion-Oberfläche meist bequemer.

### Ereignisse, Bedingungen und Aktualisierung

| Ereignis | Bedeutung |
| --- | --- |
| `nodarion_pager_alert` | Regel wurde ausgelöst oder wiederholt |
| `nodarion_pager_resolved` | Alarm wurde aufgelöst |
| `nodarion_pager_acknowledged` | Alarm wurde quittiert |

Diese Ereignisse können Home-Assistant-Automationen auslösen. Nodarion fügt keine eigenen Automations-Bedingungstypen hinzu; die internen Regelbedingungen werden in der Oberfläche konfiguriert.

Nodarion reagiert auf Home-Assistant-Zustandsänderungen und fragt Geräte nicht selbst zyklisch ab. Ein minütlicher Wartungslauf verarbeitet Zeitpläne, Timeouts, Wiederholungen, Eskalationen und lang laufende Live Activities. Konfiguration, Laufzustand und Historie werden lokal gespeichert.

### Bekannte Einschränkungen

- Live Activities benötigen einen klassischen `notify.mobile_app_*`-Dienst für den vollständigen strukturierten Payload.
- Companion App und Betriebssystem entscheiden letztlich über Darstellung und Zustellzeitpunkt.
- iOS kann zu häufige Updates drosseln und begrenzt die Lebensdauer; Nodarion drosselt und frischt lange laufende Activities regelmäßig auf.
- Nodarion überwacht vorhandene Home-Assistant-Entitäten und kommuniziert nicht direkt mit Haushaltsgeräten.

### Fehlerbehebung

- Starte Home Assistant nach einem Update neu und leere bei Darstellungsproblemen den Browser-Cache.
- Prüfe, ob ausgewählte Entitäten und Benachrichtigungsdienste noch vorhanden sind.
- Prüfe für Live Activities Companion-App-Berechtigungen, Erreichbarkeit und Home Assistant ab Version 2026.7.0.
- Fehlende Verweise erscheinen unter **Einstellungen → System → Reparaturen**.
- Diagnosen entfernen sensible Werte automatisch.

### Deinstallation

1. Lösche **Nodarion Pager** unter **Einstellungen → Geräte & Dienste**.
2. Entferne `custom_components/nodarion_pager/` oder deinstalliere die Integration über HACS.
3. Starte Home Assistant neu.

Beende aktive Live Activities vor der Deinstallation, damit ihr abschließender Löschbefehl noch zugestellt werden kann.

### Datenschutz und Sicherheit

Regelauswertung, Konfiguration und Historie bleiben in Home Assistant. Nodarion besitzt keine externe API, Cloud-Anmeldung, Analysefunktionen oder Telemetrie. Daten verlassen Home Assistant nur über ausdrücklich ausgewählte Benachrichtigungsziele. Diagnosen entfernen Entitäts-IDs, Namen, Werte, Kommentare und Benutzer-IDs. Sicherheitsprobleme bitte privat über das [Security-Advisory-Formular](https://github.com/engelsofta/nodarion-alert-manager/security/advisories/new) melden.

---

## Official Home Assistant integration readiness

This repository follows the custom integration structure and provides a UI config flow, translations, actions, diagnostics, Repairs, automated validation, installation instructions and removal instructions. A contribution to Home Assistant Core remains a separate process: core code lives under `homeassistant/components`, omits the custom `version` and `issue_tracker` manifest fields, requires tests inside the Core repository and documentation in the Home Assistant documentation repository, and may require the custom panel to be reviewed separately by the frontend project. See [OFFICIAL_INTEGRATION.md](OFFICIAL_INTEGRATION.md) for the readiness checklist and remaining work.

## Support and development

- [Report a bug](https://github.com/engelsofta/nodarion-alert-manager/issues/new?template=bug_report.yml)
- [Request a feature](https://github.com/engelsofta/nodarion-alert-manager/issues/new?template=feature_request.yml)
- [Changelog](CHANGELOG.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

Nodarion Pager is currently a custom integration and is not affiliated with or endorsed by the Home Assistant project.

## License

Apache License 2.0 © 2026 Engelsoft
