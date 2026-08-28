"""Repairs for AIS Ship Photo."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    TextSelector,
)

from .const import CONF_SEARXNG_URL, CONF_VESSEL_ENTITY


def _valid_url(value: str) -> bool:
    """Return whether a value is an HTTP(S) URL."""
    parsed_url = urlparse(value)
    return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)


class AisShipPhotoRepairFlow(RepairsFlow):
    """Repair AIS Ship Photo configuration."""

    def __init__(self, entry_id: str) -> None:
        """Initialize the repair flow."""
        self.entry_id = entry_id

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the repair form."""
        entry: ConfigEntry | None = self.hass.config_entries.async_get_entry(
            self.entry_id
        )
        if entry is None:
            return self.async_abort(reason="entry_not_found")

        errors: dict[str, str] = {}
        if user_input is not None and CONF_SEARXNG_URL in user_input:
            if not _valid_url(user_input[CONF_SEARXNG_URL]):
                errors["base"] = "invalid_url"
            elif self.hass.states.get(user_input[CONF_VESSEL_ENTITY]) is None:
                errors["base"] = "entity_not_found"
            else:
                self.hass.config_entries.async_update_entry(
                    entry, options=user_input
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_create_entry(data={})

        current = {**entry.data, **entry.options}
        data_schema = vol.Schema(
            {
                vol.Required(CONF_SEARXNG_URL): TextSelector(),
                vol.Required(
                    CONF_VESSEL_ENTITY,
                ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(data_schema, current),
            errors=errors,
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create the configuration repair flow."""
    del hass, issue_id
    entry_id = str((data or {}).get("entry_id", ""))
    return AisShipPhotoRepairFlow(entry_id)
