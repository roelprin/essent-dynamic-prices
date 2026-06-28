from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .const import DOMAIN
from .advisor import build_advisor
from .data import (
    cheapest_tariff,
    current_electricity_tariff,
    current_gas_tariff,
    group_amount,
    hour_label,
    hour_prices,
    most_expensive_tariff,
    next_electricity_tariff,
    summary,
    today,
    tomorrow,
)
from .entity import EssentDynamicEntity


class EssentDynamicSensor(EssentDynamicEntity, SensorEntity):
    def __init__(self, coordinator, key: str, name: str, icon: str | None = None, unit: str | None = None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"essent_dynamic_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit


class CurrentElectricitySensor(EssentDynamicSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = current_electricity_tariff(self.coordinator)
        return (tariff or {}).get("totalAmount")

    @property
    def extra_state_attributes(self):
        tariff = current_electricity_tariff(self.coordinator)
        return {
            "start": (tariff or {}).get("startDateTime"),
            "end": (tariff or {}).get("endDateTime"),
            "market_price": group_amount(tariff, "MARKET_PRICE"),
            "energy_tax": group_amount(tariff, "TAX"),
            "purchasing_fee": group_amount(tariff, "PURCHASING_FEE"),
            "price_ex_vat": (tariff or {}).get("totalAmountEx"),
            "vat": (tariff or {}).get("totalAmountVat"),
        }


class NextElectricitySensor(EssentDynamicSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = next_electricity_tariff(self.coordinator)
        return (tariff or {}).get("totalAmount")

    @property
    def extra_state_attributes(self):
        tariff = next_electricity_tariff(self.coordinator)
        return {
            "start": (tariff or {}).get("startDateTime"),
            "end": (tariff or {}).get("endDateTime"),
            "price_ex_vat": (tariff or {}).get("totalAmountEx"),
            "vat": (tariff or {}).get("totalAmountVat"),
        }


class GasPriceSensor(EssentDynamicSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = current_gas_tariff(self.coordinator)
        return (tariff or {}).get("totalAmount")

    @property
    def extra_state_attributes(self):
        tariff = current_gas_tariff(self.coordinator)
        return {
            "start": (tariff or {}).get("startDateTime"),
            "end": (tariff or {}).get("endDateTime"),
            "market_price": group_amount(tariff, "MARKET_PRICE"),
            "energy_tax": group_amount(tariff, "TAX"),
            "purchasing_fee": group_amount(tariff, "PURCHASING_FEE"),
        }


class TodayMetricSensor(EssentDynamicSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        electricity = (today(self.coordinator) or {}).get("electricity", {})
        mapping = {
            "electricity_min_today": "minAmount",
            "electricity_max_today": "maxAmount",
            "electricity_avg_today": "averageAmount",
        }
        return electricity.get(mapping.get(self._key))


class HourSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        day = today(self.coordinator)
        if self._key == "electricity_cheapest_hour_today":
            return hour_label(cheapest_tariff(day))
        if self._key == "electricity_most_expensive_hour_today":
            return hour_label(most_expensive_tariff(day))
        return None


class HourPricesSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        rows = hour_prices(today(self.coordinator))
        return len(rows) if rows else 0

    @property
    def extra_state_attributes(self):
        today_day = today(self.coordinator)
        tomorrow_day = tomorrow(self.coordinator)
        return {
            "today_summary": summary(today_day),
            "tomorrow_summary": summary(tomorrow_day),
            "today": hour_prices(today_day),
            "tomorrow": hour_prices(tomorrow_day),
        }




class EnergyAdvisorSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        return build_advisor(self.coordinator).get("advice")

    @property
    def extra_state_attributes(self):
        data = build_advisor(self.coordinator)
        return {key: value for key, value in data.items() if key != "advice"}


class EnergyScoreSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        return build_advisor(self.coordinator).get("score")

    @property
    def extra_state_attributes(self):
        data = build_advisor(self.coordinator)
        return {
            "rating": data.get("rating"),
            "confidence": data.get("confidence"),
            "reasons": data.get("reasons"),
            "recommended_devices": data.get("recommended_devices"),
        }


class WaitTimeSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        minutes = build_advisor(self.coordinator).get("wait_minutes")
        if minutes is None:
            return None
        return minutes

    @property
    def extra_state_attributes(self):
        data = build_advisor(self.coordinator)
        return {
            "best_hour": data.get("best_hour"),
            "best_price": data.get("best_price"),
            "advice": data.get("advice"),
        }


class PotentialSavingSensor(EssentDynamicSensor):
    @property
    def native_value(self):
        return build_advisor(self.coordinator).get("potential_saving")

    @property
    def extra_state_attributes(self):
        data = build_advisor(self.coordinator)
        return {
            "current_price": data.get("current_price"),
            "best_price": data.get("best_price"),
            "best_hour": data.get("best_hour"),
        }


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        CurrentElectricitySensor(coordinator, "electricity_current", "Stroomprijs nu", "mdi:cash", "€/kWh"),
        NextElectricitySensor(coordinator, "electricity_next", "Stroomprijs volgend uur", "mdi:clock-next", "€/kWh"),
        GasPriceSensor(coordinator, "gas_current", "Gasprijs nu", "mdi:fire", "€/m³"),
        TodayMetricSensor(coordinator, "electricity_min_today", "Laagste stroomprijs vandaag", "mdi:arrow-down-bold", "€/kWh"),
        TodayMetricSensor(coordinator, "electricity_max_today", "Hoogste stroomprijs vandaag", "mdi:arrow-up-bold", "€/kWh"),
        TodayMetricSensor(coordinator, "electricity_avg_today", "Gemiddelde stroomprijs vandaag", "mdi:chart-line", "€/kWh"),
        HourSensor(coordinator, "electricity_cheapest_hour_today", "Goedkoopste uur vandaag", "mdi:clock-star-four-points"),
        HourSensor(coordinator, "electricity_most_expensive_hour_today", "Duurste uur vandaag", "mdi:clock-alert"),
        HourPricesSensor(coordinator, "electricity_prices", "Uurprijzen", "mdi:table-clock"),
        EnergyAdvisorSensor(coordinator, "energy_advisor", "Energy advisor", "mdi:brain"),
        EnergyScoreSensor(coordinator, "energy_score", "Energy score", "mdi:trophy", "%"),
        WaitTimeSensor(coordinator, "energy_wait_time", "Wachttijd advies", "mdi:timer-sand", "min"),
        PotentialSavingSensor(coordinator, "energy_potential_saving", "Potentiële besparing", "mdi:cash-plus", "€/kWh"),
    ])
