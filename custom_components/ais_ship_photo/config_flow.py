"""Config flow for AIS Ship Photo."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import (
    CONF_SEARXNG_URL,
    CONF_VESSEL_ENTITY,
DOMAIN,
)


def _valid_url(value: str) -> bool:
    """Return whether a value is an HTTP(S) URL."""
    parsed_url = urlparse(value)
    return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)


def _data_schema() -> vol.Schema:
    """Return the shared integration settings schema."""
    return vol.Schema(
        {
            vol.Required(CONF_SEARXNG_URL): TextSelector(),
            vol.Required(
                CONF_VESSEL_ENTITY,
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
        }
    )


class AisShipPhotoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AIS Ship Photo."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the options flow for an existing config entry."""
        return AisShipPhotoOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup step."""
        errors = {}
        if user_input is not None:
            if not _valid_url(user_input[CONF_SEARXNG_URL]):
                errors["base"] = "invalid_url"
            else:
                await self.async_set_unique_id("ais_ship_photo")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="AIS Ship Photo", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema(),
            errors=errors,
        )


class AisShipPhotoOptionsFlow(OptionsFlowWithReload):
    """Handle options for an existing AIS Ship Photo entry."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage AIS Ship Photo settings."""
        errors = {}
        if user_input is not None:
            if not _valid_url(user_input[CONF_SEARXNG_URL]):
                errors["base"] = "invalid_url"
            else:
                return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(_data_schema(), current),
            errors=errors,
        )
