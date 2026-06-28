from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .data import current_electricity_tariff, today
from .entity import EssentDynamicEntity


class EssentDynamicBinarySensor(EssentDynamicEntity, BinarySensorEntity):
    def __init__(self, coordinator, key: str, name: str, icon: str | None = None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"essent_dynamic_{key}"
        self._attr_icon = icon

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
        if avg is None:
            return False

        if self._key == "cheap_hour":
            return current < avg
        if self._key == "expensive_hour":
            return current > avg

        return False


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        EssentDynamicBinarySensor(coordinator, "cheap_hour", "Goedkoop stroomuur", "mdi:thumb-up"),
        EssentDynamicBinarySensor(coordinator, "expensive_hour", "Duur stroomuur", "mdi:thumb-down"),
        EssentDynamicBinarySensor(coordinator, "negative_price", "Negatieve stroomprijs", "mdi:cash-minus"),
    ])
