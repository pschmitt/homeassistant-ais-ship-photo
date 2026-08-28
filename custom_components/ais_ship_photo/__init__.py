"""Home Assistant integration for photos of the latest AIS vessel."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_SEARXNG_URL, CONF_VESSEL_ENTITY, DOMAIN, PLATFORMS
from .coordinator import ShipPhotoCoordinator


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain."""
    del config
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AIS Ship Photo from a config entry."""
    settings = {**entry.data, **entry.options}
    coordinator = ShipPhotoCoordinator(
        hass,
        async_get_clientsession(hass),
        settings[CONF_SEARXNG_URL],
        settings[CONF_VESSEL_ENTITY],
    )
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def state_changed(event: Any) -> None:
        """Refresh the photo when the tracked vessel changes."""
        entry.async_create_background_task(
            hass,
            coordinator.async_refresh(force=True),
            "ais_ship_photo_refresh",
        )

    remove_listener: Callable[[], None] = async_track_state_change_event(
        hass,
        [entry.data[CONF_VESSEL_ENTITY]],
        state_changed,
    )
    entry.async_on_unload(remove_listener)

    await coordinator.async_refresh()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload AIS Ship Photo."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
