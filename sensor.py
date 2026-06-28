from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EssentDynamicApiClient
from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EssentDynamicCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant) -> None:
        self.api = EssentDynamicApiClient()
        super().__init__(
            hass,
            _LOGGER,
            name="Essent Dynamic Prices",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        try:
            return await self.api.async_get_prices()
        except Exception as err:
            raise UpdateFailed(f"Fout bij ophalen Essent prijzen: {err}") from err
