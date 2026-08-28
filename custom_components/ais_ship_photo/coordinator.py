"""SearXNG search and image-proxy handling for AIS Ship Photo."""

from __future__ import annotations

import asyncio
import html
import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urljoin

from aiohttp import ClientError, ClientSession
from homeassistant.core import HomeAssistant, callback

_LOGGER = logging.getLogger(__name__)

_MARINE_TRAFFIC_PROXY = re.compile(
    r"/image_proxy\?url=https%3A%2F%2Fwww\.marinetraffic\.com%2FgetAssetDefaultPhoto"
    r"%2F%3Fphoto_size%3D800%26asset_id%3D[0-9]+%26asset_type_id%3D0&h=[0-9a-f]+"
)
_VESSEL_FINDER_PROXY = re.compile(
    r"/image_proxy\?url=https%3A%2F%2Fstatic\.vesselfinder\.net%2Fship-photo%2F[^&\"]+"
    r"&h=[0-9a-f]+"
)
_RETRY_INTERVAL = timedelta(minutes=5)


class ShipPhotoCoordinator:
    """Keep the latest vessel photo and its lookup metadata."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        searxng_url: str,
        vessel_entity: str,
    ) -> None:
        self.hass = hass
        self.session = session
        self.searxng_url = searxng_url.rstrip("/")
        self.vessel_entity = vessel_entity
        self._image: bytes | None = None
        self._content_type = "image/jpeg"
        self._mmsi = ""
        self._vessel_name = ""
        self._provider = ""
        self._photo_url = ""
        self._last_attempt: datetime | None = None
        self._last_updated: datetime | None = None
        self._error = ""
        self._listeners: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        """Return whether a current photo is available."""
        return self._image is not None

    @property
    def image(self) -> bytes | None:
        """Return the cached image bytes."""
        return self._image

    @property
    def content_type(self) -> str:
        """Return the cached image content type."""
        return self._content_type

    @property
    def vessel_name(self) -> str:
        """Return the current vessel name."""
        return self._vessel_name

    @property
    def attributes(self) -> dict[str, str | None]:
        """Return diagnostic attributes for the camera."""
        return {
            "vessel_name": self._vessel_name or None,
            "mmsi": self._mmsi or None,
            "provider": self._provider or None,
            "photo_url": self._photo_url or None,
            "last_updated": self._last_updated.isoformat()
            if self._last_updated
            else None,
            "error": self._error or None,
        }

    @property
    def needs_refresh(self) -> bool:
        """Return whether the current entity needs a lookup."""
        state = self.hass.states.get(self.vessel_entity)
        if state is None:
            return False
        mmsi = str(state.attributes.get("mmsi", ""))
        if mmsi != self._mmsi:
            return True
        return (
            self._last_attempt is None
            or datetime.now(UTC) - self._last_attempt >= _RETRY_INTERVAL
        )

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for coordinator updates."""
        self._listeners.append(listener)

        @callback
        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    async def async_refresh(self, *, force: bool = False) -> None:
        """Search for and cache the current vessel photo."""
        state = self.hass.states.get(self.vessel_entity)
        if state is None:
            self._set_error(f"Vessel entity {self.vessel_entity} is unavailable")
            return

        vessel_name = str(
            state.attributes.get("ship_name") or state.state or "Unknown ship"
        )
        mmsi = str(state.attributes.get("mmsi") or "")
        if not mmsi:
            self._set_error("Tracked vessel has no MMSI")
            return
        if (
            not force
            and mmsi == self._mmsi
            and self._last_attempt is not None
            and datetime.now(UTC) - self._last_attempt < _RETRY_INTERVAL
        ):
            return

        async with self._lock:
            self._last_attempt = datetime.now(UTC)
            self._vessel_name = vessel_name
            self._mmsi = mmsi
            self._provider = ""
            self._photo_url = ""
            self._image = None
            self._error = ""
            query = " ".join(part for part in (vessel_name, mmsi) if part)
            search_url = f"{self.searxng_url}/search?{urlencode({'q': query, 'categories': 'images'})}"

            try:
                async with self.session.get(
                    search_url,
                    headers={
                        "Accept": "text/html",
                        "User-Agent": "Home Assistant AIS ship photo camera",
                    },
                    timeout=15,
                ) as response:
                    response.raise_for_status()
                    search_html = html.unescape(await response.text())

                proxy_path = _MARINE_TRAFFIC_PROXY.search(search_html)
                provider = "MarineTraffic"
                if proxy_path is None:
                    proxy_path = _VESSEL_FINDER_PROXY.search(search_html)
                    provider = "VesselFinder"
                if proxy_path is None:
                    self._set_error("No MarineTraffic or VesselFinder photo found")
                    _LOGGER.debug(
                        "No photo result found for %s (%s)", vessel_name, mmsi
                    )
                    return

                photo_url = urljoin(f"{self.searxng_url}/", proxy_path.group(0))
                async with self.session.get(
                    photo_url,
                    headers={"User-Agent": "Home Assistant AIS ship photo camera"},
                    timeout=20,
                ) as response:
                    response.raise_for_status()
                    image = await response.read()
                    content_type = response.headers.get("Content-Type", "image/jpeg")

                if not image:
                    self._set_error("Photo proxy returned an empty image")
                    return
                self._image = image
                self._content_type = content_type.split(";", 1)[0]
                self._provider = provider
                self._photo_url = photo_url
                self._last_updated = datetime.now(UTC)
                _LOGGER.debug(
                    "Updated %s photo for %s (%s) via %s",
                    self.vessel_entity,
                    vessel_name,
                    mmsi,
                    provider,
                )
            except (ClientError, asyncio.TimeoutError) as err:
                self._set_error(f"Photo lookup failed: {err}")
                _LOGGER.warning("AIS ship photo lookup failed for %s: %s", mmsi, err)
            finally:
                self._notify_listeners()

    def _set_error(self, error: str) -> None:
        """Set an error while clearing the old photo."""
        self._image = None
        self._error = error

    def _notify_listeners(self) -> None:
        """Notify entities that coordinator data changed."""
        for listener in tuple(self._listeners):
            listener()
