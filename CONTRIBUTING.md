# Contributing

Contributions, bug reports and feature ideas are welcome.

## Before opening an issue

- Update to the latest release.
- Restart Home Assistant and clear the browser cache for frontend issues.
- Search existing issues.
- Remove tokens, private URLs, personal names, entity IDs and other sensitive data from logs or diagnostics.

## Development

1. Fork and clone the repository.
2. Create a focused branch.
3. Install the test dependencies: `python -m pip install pytest ruff homeassistant`.
4. Run `python -m pytest` and `ruff check custom_components tests`.
5. Check the frontend with `node --check custom_components/nodarion_pager/frontend/nodarion-pager-panel.js`.
6. Open a pull request describing the user-visible impact.

By contributing, you agree that your changes are licensed under Apache License 2.0.
