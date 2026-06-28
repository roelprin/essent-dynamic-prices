from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    return {
        "prices_count": len(data.get("prices", [])),
        "dates": [item.get("date") for item in data.get("prices", [])],
        "raw_data_available": bool(data),
    }
