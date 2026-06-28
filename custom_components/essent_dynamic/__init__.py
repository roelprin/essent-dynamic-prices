from __future__ import annotations

from datetime import timedelta
import logging
import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, API_URL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "binary_sensor"]


class EssentDynamicCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Essent Dynamic Prices",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        headers = {
            "Accept": "application/json",
            "x-request-origin": "client",
            "User-Agent": "Home Assistant Essent Dynamic Prices",
        }

        try:
            async with async_timeout.timeout(20):
                async with aiohttp.ClientSession() as session:
                    async with session.get(API_URL, headers=headers) as response:
                        if response.status != 200:
                            text = await response.text()
                            raise UpdateFailed(f"Essent API gaf status {response.status}: {text[:150]}")
                        return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Fout bij ophalen Essent prijzen: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = EssentDynamicCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
