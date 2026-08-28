"""Home Assistant integration for photos of the latest AIS vessel."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.issue_registry import IssueSeverity

from .const import CONF_SEARXNG_URL, CONF_VESSEL_ENTITY, DOMAIN, PLATFORMS
from .coordinator import ShipPhotoCoordinator


def _valid_url(value: str) -> bool:
    """Return whether a value is an HTTP(S) URL."""
    parsed_url = urlparse(value)
    return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)


def _update_config_issues(
    hass: HomeAssistant, entry: ConfigEntry, settings: dict[str, Any]
) -> None:
    """Create or clear actionable configuration issues."""
    vessel_issue_id = f"vessel_entity_missing_{entry.entry_id}"
    if hass.states.get(settings[CONF_VESSEL_ENTITY]) is None:
        ir.async_create_issue(
            hass,
            DOMAIN,
            vessel_issue_id,
            data={"entry_id": entry.entry_id},
            is_fixable=True,
            is_persistent=True,
            issue_domain=DOMAIN,
            severity=IssueSeverity.ERROR,
            translation_key="vessel_entity_missing",
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, vessel_issue_id)

    url_issue_id = f"invalid_searxng_url_{entry.entry_id}"
    if _valid_url(settings[CONF_SEARXNG_URL]):
        ir.async_delete_issue(hass, DOMAIN, url_issue_id)
    else:
        ir.async_create_issue(
            hass,
            DOMAIN,
            url_issue_id,
            data={"entry_id": entry.entry_id},
            is_fixable=True,
            is_persistent=True,
            issue_domain=DOMAIN,
            severity=IssueSeverity.ERROR,
            translation_key="invalid_searxng_url",
        )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain."""
    del config
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AIS Ship Photo from a config entry."""
    settings = {**entry.data, **entry.options}
    _update_config_issues(hass, entry, settings)
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
        _update_config_issues(hass, entry, settings)
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
