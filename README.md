# Essent Dynamic Prices for Home Assistant

![Essent Dynamic Prices](images/logo.svg)

A Home Assistant custom integration for Essent dynamic energy prices.

This integration reads Essent's public dynamic pricing endpoint and exposes current electricity, gas and hourly price data in Home Assistant.

> Status: active development. This is not an official Essent integration.

## Features

### Sensors

- ⚡ Current electricity price
- ➡️ Next hour electricity price
- 🔥 Current gas price
- 📉 Lowest electricity price today
- 📈 Highest electricity price today
- 📊 Average electricity price today
- 🕐 Cheapest hour today
- 🕘 Most expensive hour today
- 📋 Hourly prices with detailed attributes

### Binary sensors

- 🟢 Cheap electricity hour
- 🔴 Expensive electricity hour
- ⚫ Negative electricity price

### Attributes

The hourly prices sensor exposes:

- `today`
- `tomorrow`
- `today_summary`
- `tomorrow_summary`

The current electricity price sensor exposes:

- market price
- energy tax
- purchasing fee
- VAT
- price excluding VAT

## Installation via HACS

1. Open **HACS**.
2. Go to **Integrations**.
3. Open the three-dot menu.
4. Choose **Custom repositories**.
5. Add this repository URL.
6. Category: **Integration**.
7. Install **Essent Dynamic Prices**.
8. Restart Home Assistant.
9. Add the integration via **Settings → Devices & services → Add integration**.

## Manual installation

Copy this folder:

```text
custom_components/essent_dynamic
```

to:

```text
/config/custom_components/essent_dynamic
```

Restart Home Assistant.

## Dashboard example

Install **ApexCharts Card** through HACS and use the `Uurprijzen` sensor attributes to draw today and tomorrow price charts.

Example:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Essent stroomprijzen vandaag
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Nu
series:
  - entity: sensor.essent_dynamic_prices_uurprijzen
    name: Vandaag
    type: column
    data_generator: |
      const data = entity.attributes.today || [];
      return data.map((item) => {
        return [new Date(item.start).getTime(), item.price];
      });
apex_config:
  yaxis:
    decimalsInFloat: 3
    title:
      text: €/kWh
```

If your entity is named differently, replace the entity ID.

## Notes about tomorrow prices

Tomorrow's electricity prices are only available after Essent publishes them. Until then, the `tomorrow` attribute is empty and `tomorrow_summary` contains null values.

## Development

The integration structure:

```text
custom_components/essent_dynamic/
├── api.py
├── binary_sensor.py
├── config_flow.py
├── const.py
├── coordinator.py
├── data.py
├── diagnostics.py
├── entity.py
├── manifest.json
├── sensor.py
└── translations/
```

## License

MIT
