from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .helpers import (
    today, tomorrow, current_electricity_tariff, next_electricity_tariff,
    current_gas_tariff, cheapest_tariff, most_expensive_tariff, hour_label,
    group_amount, hour_prices, summary
)


class EssentBaseSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name, icon=None, unit=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"essent_dynamic_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "essent_dynamic_prices")},
            name="Essent Dynamic Prices",
            manufacturer="Essent",
            model="Dynamic pricing API",
        )


class CurrentElectricitySensor(EssentBaseSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = current_electricity_tariff(self.coordinator)
        return tariff.get("totalAmount") if tariff else None

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


class NextElectricitySensor(EssentBaseSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = next_electricity_tariff(self.coordinator)
        return tariff.get("totalAmount") if tariff else None

    @property
    def extra_state_attributes(self):
        tariff = next_electricity_tariff(self.coordinator)
        return {
            "start": (tariff or {}).get("startDateTime"),
            "end": (tariff or {}).get("endDateTime"),
            "price_ex_vat": (tariff or {}).get("totalAmountEx"),
            "vat": (tariff or {}).get("totalAmountVat"),
        }


class TodayMetricSensor(EssentBaseSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        day = today(self.coordinator)
        electricity = (day or {}).get("electricity", {})
        if self._key == "electricity_min_today":
            return electricity.get("minAmount")
        if self._key == "electricity_max_today":
            return electricity.get("maxAmount")
        if self._key == "electricity_avg_today":
            return electricity.get("averageAmount")
        return None


class GasSensor(EssentBaseSensor):
    _attr_device_class = SensorDeviceClass.MONETARY

    @property
    def native_value(self):
        tariff = current_gas_tariff(self.coordinator)
        return tariff.get("totalAmount") if tariff else None

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


class HourSensor(EssentBaseSensor):
    @property
    def native_value(self):
        day = today(self.coordinator)
        if self._key == "electricity_cheapest_hour_today":
            return hour_label(cheapest_tariff(day))
        if self._key == "electricity_most_expensive_hour_today":
            return hour_label(most_expensive_tariff(day))
        return None


class HourPricesSensor(EssentBaseSensor):
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




class SummarySensor(EssentBaseSensor):
    @property
    def native_value(self):
        day = today(self.coordinator)
        info = summary(day)

        if self._key == "electricity_spread_today":
            return info.get("spread")

        if self._key == "electricity_hours_below_average_today":
            return info.get("hours_below_average")

        if self._key == "electricity_hours_above_average_today":
            return info.get("hours_above_average")

        if self._key == "electricity_negative_market_hours_today":
            return info.get("negative_market_hours")

        if self._key == "electricity_cheap_block_today":
            block = info.get("cheapest_block_below_average")
            if not block:
                return None
            start = block.get("start")
            end = block.get("end")
            if isinstance(end, str) and "T" in end:
                end = end.split("T")[1][:5]
            return f"{start}-{end}"

        if self._key == "electricity_cheap_block_average_today":
            block = info.get("cheapest_block_below_average")
            return block.get("average") if block else None

        if self._key == "electricity_smart_advice":
            current = current_electricity_tariff(self.coordinator)
            current_price = (current or {}).get("totalAmount")
            avg = info.get("average")
            cheapest_hour = info.get("cheapest_hour")
            cheapest_price = info.get("cheapest_price")
            block = info.get("cheapest_block_below_average")

            if current_price is None:
                return "Geen prijsdata beschikbaar"
            if current_price < 0:
                return "Stroomprijs is negatief"
            if avg is not None and current_price < avg:
                return "Nu is stroom goedkoper dan gemiddeld"
            if cheapest_hour and cheapest_price is not None:
                return f"Goedkoopste uur vandaag is {cheapest_hour} (€{cheapest_price:.3f}/kWh)"
            if block:
                return f"Goedkoop blok vandaag vanaf {block.get('start')}"
            return "Geen advies beschikbaar"

        return None

    @property
    def extra_state_attributes(self):
        return summary(today(self.coordinator))


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        CurrentElectricitySensor(coordinator, "electricity_current", "Stroomprijs nu", "mdi:cash", "€/kWh"),
        NextElectricitySensor(coordinator, "electricity_next", "Stroomprijs volgend uur", "mdi:clock-next", "€/kWh"),
        GasSensor(coordinator, "gas_current", "Gasprijs nu", "mdi:fire", "€/m³"),
        TodayMetricSensor(coordinator, "electricity_min_today", "Laagste stroomprijs vandaag", "mdi:arrow-down-bold", "€/kWh"),
        TodayMetricSensor(coordinator, "electricity_max_today", "Hoogste stroomprijs vandaag", "mdi:arrow-up-bold", "€/kWh"),
        TodayMetricSensor(coordinator, "electricity_avg_today", "Gemiddelde stroomprijs vandaag", "mdi:chart-line", "€/kWh"),
        HourSensor(coordinator, "electricity_cheapest_hour_today", "Goedkoopste uur vandaag", "mdi:clock-star-four-points"),
        HourSensor(coordinator, "electricity_most_expensive_hour_today", "Duurste uur vandaag", "mdi:clock-alert"),
        HourPricesSensor(coordinator, "electricity_prices", "Uurprijzen", "mdi:table-clock"),

        SummarySensor(coordinator, "electricity_spread_today", "Prijsverschil vandaag", "mdi:delta", "€/kWh"),
        SummarySensor(coordinator, "electricity_hours_below_average_today", "Uren onder gemiddelde", "mdi:clock-check-outline"),
        SummarySensor(coordinator, "electricity_hours_above_average_today", "Uren boven gemiddelde", "mdi:clock-alert-outline"),
        SummarySensor(coordinator, "electricity_negative_market_hours_today", "Uren negatieve beursprijs", "mdi:cash-minus"),
        SummarySensor(coordinator, "electricity_cheap_block_today", "Goedkoop blok vandaag", "mdi:clock-fast"),
        SummarySensor(coordinator, "electricity_cheap_block_average_today", "Gemiddelde prijs goedkoop blok", "mdi:chart-bell-curve", "€/kWh"),
        SummarySensor(coordinator, "electricity_smart_advice", "Slim advies", "mdi:lightbulb-on-outline"),
    ])
