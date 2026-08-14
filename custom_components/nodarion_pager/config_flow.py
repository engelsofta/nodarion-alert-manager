"""Config flow for Nodarion Pager."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, NAME


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the single Pager instance."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle setup."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
