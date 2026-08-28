# AIS Ship Photo for Home Assistant

Provides a `camera.last_passing_ship_photo` entity for the latest vessel seen by
the AIS Ship Tracker add-on. The integration searches a configured SearXNG
instance and retrieves the result through SearXNG's signed image proxy.

MarineTraffic results are preferred; VesselFinder is used as a fallback. The
camera caches the image and exposes the vessel name, MMSI, provider, proxy URL,
and lookup status as attributes. The SearXNG URL and tracked vessel sensor can
be changed at any time from the integration's Configure menu; changes reload
the entry automatically.
and lookup errors as entity attributes.

Licensed under the GNU General Public License version 3.0 or later.
