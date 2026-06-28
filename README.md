# Essent Dynamic Prices for Home Assistant

Home Assistant custom integration for Essent dynamic energy prices.

## Features

- Current electricity price
- Next hour electricity price
- Current gas price
- Lowest, highest and average electricity price today
- Cheapest and most expensive hour today
- Hourly prices for dashboard charts
- Cheap hour, expensive hour and negative price binary sensors
- Detailed attributes for market price, taxes, VAT and purchasing fee

## Installation via HACS

1. Open HACS.
2. Go to Integrations.
3. Add this repository as a custom repository.
4. Category: Integration.
5. Install **Essent Dynamic Prices**.
6. Restart Home Assistant.
7. Add the integration via Settings → Devices & services.

## Dashboard

The `Uurprijzen` sensor exposes `today`, `tomorrow`, `today_summary` and `tomorrow_summary` attributes for ApexCharts dashboards.

## Status

In active development.
