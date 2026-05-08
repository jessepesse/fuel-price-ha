# Fuel Price Sensor — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration that tracks cheapest fuel prices by city. Prices update automatically every 30 minutes.

## Sensors

Three sensors are created per configured city:

| Sensor | Unit | Description |
|--------|------|-------------|
| `sensor.fuel_price_<city>_95_e10` | €/l | Cheapest 95 E10 |
| `sensor.fuel_price_<city>_98_e5` | €/l | Cheapest 98 E5 |
| `sensor.fuel_price_<city>_diesel` | €/l | Cheapest diesel |

Each sensor includes attributes: cheapest station name, last updated time, and a full list of the 5 cheapest stations with prices.

## Dashboard cards

Replace `<city>` with your configured city name.

### Entity Card — cheapest price only

The simplest option, no extra integrations required.

```yaml
type: entity
entity: sensor.fuel_price_<city>_95_e10
```

### Mushroom Template Card — cheapest station + price

Requires [Mushroom](https://github.com/piitaya/lovelace-mushroom) (available via HACS).

```yaml
type: custom:mushroom-template-card
primary: "{{ state_attr('sensor.fuel_price_<city>_95_e10', 'cheapest_station') }}"
secondary: "{{ states('sensor.fuel_price_<city>_95_e10') }} €/l — {{ state_attr('sensor.fuel_price_<city>_95_e10', 'cheapest_updated') }}"
icon: mdi:gas-station
icon_color: green
tap_action:
  action: more-info
```

### Markdown Card — top 5 list for one fuel type

```yaml
type: markdown
content: >
  ## ⛽ {{ state_attr('sensor.fuel_price_<city>_95_e10', 'fuel_type') }} — {{ state_attr('sensor.fuel_price_<city>_95_e10', 'city') | capitalize }}

  {% for s in state_attr('sensor.fuel_price_<city>_95_e10', 'stations') %}
  **{{ loop.index }}.** {{ s.station }} — {{ s.price }} €/l *({{ s.updated }})*
  {% endfor %}
```

### Markdown Card — all fuel types combined

```yaml
type: markdown
content: >
  ## ⛽ {{ state_attr('sensor.fuel_price_<city>_95_e10', 'city') | capitalize }}

  ### 95 E10
  {% for s in state_attr('sensor.fuel_price_<city>_95_e10', 'stations') %}
  {{ loop.index }}. {{ s.station }} — **{{ s.price }} €/l** *({{ s.updated }})*
  {% endfor %}

  ### 98 E5
  {% for s in state_attr('sensor.fuel_price_<city>_98_e5', 'stations') %}
  {{ loop.index }}. {{ s.station }} — **{{ s.price }} €/l** *({{ s.updated }})*
  {% endfor %}

  ### Diesel
  {% for s in state_attr('sensor.fuel_price_<city>_diesel', 'stations') %}
  {{ loop.index }}. {{ s.station }} — **{{ s.price }} €/l** *({{ s.updated }})*
  {% endfor %}
```

## Installation via HACS

1. Open HACS → Integrations → three dots → **Custom repositories**
2. Add URL: `https://github.com/jessepesse/fuel-price-ha`
   Category: **Integration**
3. Search for "Fuel Price" and install
4. Restart Home Assistant

## Manual installation

Copy the `custom_components/fuel_price` folder to your HA `config/custom_components/` directory and restart.

## Setup

**Settings → Devices & Services → Add Integration → Fuel Price Sensor**

Enter the base URL of a compatible fuel price service and the city name (e.g. `oulu`, `helsinki`, `tampere`). You can add multiple cities by repeating the process.
