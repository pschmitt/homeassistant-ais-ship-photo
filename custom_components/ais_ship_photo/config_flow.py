"""Config flow for AIS Ship Photo."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

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
            await self.async_set_unique_id("ais_ship_photo")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="AIS Ship Photo", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SEARXNG_URL,
                ): cv.url,
                vol.Required(
                    CONF_VESSEL_ENTITY,
                ): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
