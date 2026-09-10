# Home Assistant Core submission readiness

Nodarion Pager 1.0 is distributed as a custom integration through HACS. This document separates the work already completed from the work that must happen in the Home Assistant repositories before it can become a built-in integration.

## Current foundation

- UI-based, single-entry config flow
- unique config entry protection
- asynchronous setup and unload
- event-driven state handling with a bounded housekeeping interval
- translations and service action descriptions
- local storage and privacy-conscious diagnostics
- Home Assistant Repairs for missing rule references
- integration brand assets
- user installation, configuration, limitation, troubleshooting and removal documentation
- automated Python, frontend, Hassfest, HACS, release and privacy validation

## Required Core contribution work

The official submission must be made as a focused pull request to `home-assistant/core`. It cannot be completed merely by publishing this repository.

1. Move the integration package to `homeassistant/components/nodarion_pager`.
2. Remove the custom-only `version` and `issue_tracker` fields from the Core manifest and change `documentation` to `https://www.home-assistant.io/integrations/nodarion_pager`.
3. Adapt runtime storage to the exact `ConfigEntry.runtime_data` conventions of the target Core release.
4. Add full config-flow coverage and focused tests for setup, unload, rule evaluation, storage migration, services, diagnostics and Live Activity delivery inside the Core test suite.
5. Add `quality_scale.yaml` only for rules demonstrated by those tests and the submitted documentation. New integrations must satisfy every applicable Bronze rule.
6. Submit end-user documentation to the Home Assistant documentation repository.
7. Submit branding to the Home Assistant brands repository.
8. Agree with Home Assistant maintainers on the custom administration panel. A built-in frontend panel can require a separate or separate frontend contribution; the initial Core pull request may need a smaller scope.
9. Confirm with maintainers that a general-purpose local alert manager is eligible as a Core integration. Core normally prioritizes established products or services and asks new integration pull requests to remain small.

## Suggested submission scope

For the best chance of review, start with the smallest useful backend capability and its tests, then follow with the administration panel and extended alert features. Keep the HACS edition fully featured while the Core proposal is discussed.

## References

- [Contributing an integration to Home Assistant Core](https://developers.home-assistant.io/docs/core/integration/contributing_to_core/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
- [Quality Scale checklist](https://developers.home-assistant.io/docs/core/integration-quality-scale/checklist/)
- [Integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
