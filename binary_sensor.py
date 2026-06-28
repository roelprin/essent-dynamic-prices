from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .coordinator import EssentDynamicCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]

OBSOLETE_UNIQUE_IDS = {
    # Experimental v1.x / v2.x breakdown sensors, now exposed as attributes.
    "essent_dynamic_electricity_market_current",
    "essent_dynamic_electricity_tax_current",
    "essent_dynamic_electricity_fee_current",
    "essent_dynamic_electricity_purchasing_fee_current",

    # Experimental tomorrow sensors, now exposed through Uurprijzen attributes.
    "essent_dynamic_electricity_min_tomorrow",
    "essent_dynamic_electricity_max_tomorrow",
    "essent_dynamic_electricity_avg_tomorrow",
    "essent_dynamic_electricity_cheapest_hour_tomorrow",
    "essent_dynamic_electricity_most_expensive_hour_tomorrow",

    # Experimental smart-summary sensors, now exposed through Uurprijzen attributes.
    "essent_dynamic_electricity_spread_today",
    "essent_dynamic_electricity_hours_below_average_today",
    "essent_dynamic_electricity_hours_above_average_today",
    "essent_dynamic_electricity_negative_market_hours_today",
    "essent_dynamic_electricity_cheap_block_today",
    "essent_dynamic_electricity_cheap_block_average_today",
    "essent_dynamic_electricity_smart_advice",

    # Experimental active-hour binary sensors.
    "essent_dynamic_cheapest_hour",
    "essent_dynamic_most_expensive_hour",
}


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old experimental entities to the compact v3 entity model."""
    if entry.version < 2:
        registry = er.async_get(hass)

        for entity_id, registry_entry in list(registry.entities.items()):
            if (
                registry_entry.config_entry_id == entry.entry_id
                and registry_entry.unique_id in OBSOLETE_UNIQUE_IDS
            ):
                _LOGGER.info("Removing obsolete Essent Dynamic entity: %s", entity_id)
                registry.async_remove(entity_id)

        hass.config_entries.async_update_entry(entry, version=2)

    return True


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
