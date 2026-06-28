from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .helpers import current_electricity_tariff, today


class EssentBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name, icon=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"essent_dynamic_{key}"
        self._attr_icon = icon

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "essent_dynamic_prices")},
            name="Essent Dynamic Prices",
            manufacturer="Essent",
            model="Dynamic pricing API",
        )

    @property
    def is_on(self):
        tariff = current_electricity_tariff(self.coordinator)
        current = (tariff or {}).get("totalAmount")
        day = today(self.coordinator)

        if current is None:
            return False

        if self._key == "negative_price":
            return current < 0

        avg = (day or {}).get("electricity", {}).get("averageAmount")
        if self._key == "cheap_hour":
            return avg is not None and current < avg
        if self._key == "expensive_hour":
            return avg is not None and current > avg

        return False


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        EssentBinarySensor(coordinator, "cheap_hour", "Goedkoop stroomuur", "mdi:thumb-up"),
        EssentBinarySensor(coordinator, "expensive_hour", "Duur stroomuur", "mdi:thumb-down"),
        EssentBinarySensor(coordinator, "negative_price", "Negatieve stroomprijs", "mdi:cash-minus"),
    ])
