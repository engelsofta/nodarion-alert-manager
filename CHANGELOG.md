# Changelog

## 0.7.6

- Separated entity search text from the selected entity in the rule wizard
- Restored reliable searches by both friendly name and entity ID

## 0.7.5

- Removed the redundant condition-step preview from the rule wizard

## 0.7.4

- Enlarged the rule wizard to use nearly the full available viewport
- Increased usable step space while keeping the summary and actions fixed

## 0.7.3

- Added a persistent live rule summary to every wizard step
- Reused the same summary as the final confirmation view

## 0.7.2

- Made the final rule summary update live when advanced behavior changes

## 0.7.1

- Reworked rule creation into a clear four-step assistant
- Enlarged and redesigned the entity search results
- Improved automatic detection of numeric sensor entities
- Made the rule-filter reset action compact and space-saving

## 0.7.0

- Added versioned storage migration, reliable queued saves and per-rule evaluation locks
- Added maintenance and per-rule pauses, schedules, additional AND/OR conditions and escalation stages
- Added rule import/export, duplication, alarm comments, diagnostics, repairs and Home Assistant services
- Reduced live refresh payloads and added history pagination support
- Added missing-entity states, filter reset controls and CI tests/linting

## 0.6.6

- Added a test button for each notification target in settings
- Test delivery now reports Home Assistant service errors directly in the UI

## 0.6.5

- Added a configurable grace period before unavailable entities raise an alert (60 seconds by default)
- Applied the same availability grace period consistently to heartbeat rules

## 0.6.4

- Ein Doppelklick leert ein Filterfeld beziehungsweise setzt eine Auswahl auf „Alle“ zurück.
- Die Regelliste zeigt Gesamtzahl und aktuell gefilterte Trefferzahl live an.

## 0.6.3

- Neu aktivierte Empfänger werden nicht mehr automatisch bestehenden Regeln zugeordnet.
- Alte Regeln ohne explizite Empfängerzuordnung starten sicher ohne Empfänger, statt automatisch alle aktiven Ziele zu übernehmen.

## 0.6.2

- Benachrichtigungsempfänger können einen eigenen Anzeigenamen und eine individuelle Farbe erhalten.
- Empfängerfarben werden als Punkte in Regelliste und Regelauswahl dargestellt.

## 0.6.1

- Die Regelliste bietet jetzt kombinierbare Filter für Typ, Priorität, Empfänger und Status.
- Die Empfängerauswahl wird automatisch aus den tatsächlich vorhandenen Tabellenwerten erzeugt.

- Benachrichtigungsempfänger können jetzt pro Regel ausgewählt, in der Regelliste angezeigt und nach Empfänger sortiert werden.

## 0.6.0

- Neuer Regeltyp **Heartbeat**: alarmiert, wenn sich der Wert einer Entität innerhalb der eingestellten Zeit nicht ändert.
- Eine neue Wertänderung setzt den Heartbeat automatisch zurück und löst eine Entwarnung aus.
- Einfache Einrichtung über Entität und Zeitlimit in Minuten; erweiterte Alarmoptionen bleiben optional.

## 0.5.5

- Improve contrast and status colors when Home Assistant uses a light theme

## 0.5.4

- Show the current entity value before the configured rule condition

## 0.5.3

- Reduced chart point size and line weight for a cleaner history graph

## 0.5.2

- Display Home Assistant's localized semantic state labels instead of raw on/off values

## 0.5.1

- Keep keyboard focus in search and filter controls during live updates

## 0.5.0

- Redesigned rule editor around analog, digital/I/O and fault modes
- Automatically infer the rule mode from the selected entity
- Offer known entity states directly in a dropdown
- Hide numeric-only controls for digital and fault rules

## 0.4.1

- Refined chart line weights, points, grid and alarm shading
- Added an interactive vertical crosshair with timestamp, value and alarm state

## 0.4.0

- Added a per-rule history chart using Home Assistant recorder data
- Highlighted threshold violations and binary/fault periods directly in the chart
- Added 6-hour, 24-hour and 7-day chart ranges

## 0.3.5

- Added text and category filters to the rules and history tables

## 0.3.4

- Wait for Home Assistant startup and a configurable grace period before evaluating rules
- Ignore transient entity changes during the startup grace period

## 0.3.3

- Pause live refresh while settings are being edited so unsaved checkbox changes remain intact

## 0.3.2

- Changed the sidebar label to Engelsoft Pager
- Replaced the unavailable pager icon with the supported bell-alert icon

## 0.3.1

- Entity names in rules, alarms and history now open Home Assistant's native more-info dialog

## 0.3.0

- Added configurable forwarding to modern notify entities and legacy notify actions
- Added multiple target selection for HA Companion App, Telegram and other notifiers
- Added severity filters and optional resolved notifications
- Isolated notifier failures from the monitoring engine

## 0.2.0

- Added dedicated threshold, bit/I/O and fault rule types
- Added transient Home Assistant notifications for active fault rules
- Added a prominent current-value column to the rules table
- Follow the Home Assistant language automatically
- Replaced the header placeholder with a reliable inline Pager mark

## 0.1.0

- Initial HACS-ready release
- Persistent rule engine and alarm history
- Delayed conditions, hysteresis, cooldown and repetition
- Admin-only German/English sidebar interface
- Home Assistant event integration
