"""Config flow for AIS Ship Photo."""

from __future__ import annotations

from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import TextSelector

from .const import (
    CONF_SEARXNG_URL,
    CONF_VESSEL_ENTITY,
    DOMAIN,
)


class AisShipPhotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIS Ship Photo."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}
        if user_input is not None:
            parsed_url = urlparse(user_input[CONF_SEARXNG_URL])
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                errors["base"] = "invalid_url"
            else:
                await self.async_set_unique_id("ais_ship_photo")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="AIS Ship Photo", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SEARXNG_URL,
                ): TextSelector(),
                vol.Required(
                    CONF_VESSEL_ENTITY,
                ): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
