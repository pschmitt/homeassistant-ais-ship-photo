"""Camera platform for AIS Ship Photo."""

from __future__ import annotations

from homeassistant.components.camera import CameraEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ShipPhotoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up the AIS ship photo camera."""
    coordinator: ShipPhotoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ShipPhotoCamera(coordinator)])


class ShipPhotoCamera(CameraEntity):
    """Camera showing the latest AIS vessel photo."""

    _attr_icon = "mdi:ferry"
    _attr_has_entity_name = True

    def __init__(self, coordinator: ShipPhotoCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_unique_id = "last_passing_ship_photo"
        self._attr_name = "Last Passing Ship Photo"

    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def available(self) -> bool:
        """Return whether a photo is currently cached."""
        return self.coordinator.available

    @property
    def extra_state_attributes(self):
        """Expose lookup details for debugging."""
        return self.coordinator.attributes

    async def async_camera_image(self, width=None, height=None) -> bytes | None:
        """Return the cached vessel photo."""
        if self.coordinator.needs_refresh:
            await self.coordinator.async_refresh()
        self._attr_content_type = self.coordinator.content_type
        return self.coordinator.image
