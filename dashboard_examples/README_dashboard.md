# Dashboard voorbeelden

## Vereist
Installeer eerst via HACS:
- ApexCharts Card

## Gebruik
1. Ga naar je dashboard.
2. Klik op Bewerken.
3. Kies + Kaart toevoegen.
4. Kies Handmatige kaart.
5. Plak de YAML uit `essent_dashboard_cards.yaml`.

## Entity ID aanpassen
Controleer vooral de Uurprijzen entity. Bij Roel was dat:

```yaml
sensor.essent_dynamic_prices_uurprijzen_2
```

Als jouw entity anders heet, vervang die naam in de ApexCharts-kaarten.
