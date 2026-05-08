# Fuel Price Sensor — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/jessepesse/fuel-price-ha?label=release)](https://github.com/jessepesse/fuel-price-ha/releases/latest)
[![Pre-release](https://img.shields.io/github/v/release/jessepesse/fuel-price-ha?include_prereleases&label=dev)](https://github.com/jessepesse/fuel-price-ha/releases)

Home Assistant integration that tracks fuel prices by city. Prices update automatically every 30 minutes.

## Sensors

The integration creates three sensors per fuel type (95 E10, 98 E5, Diesel). The sensor behavior depends on the mode selected during setup:

### Cheapest mode

Shows the cheapest available price in the city. Sensor names follow the pattern `sensor.fuel_price_<city>_<fuel>`.

| Attribute | Description |
|-----------|-------------|
| `cheapest_station` | Name of the cheapest station |
| `cheapest_updated` | When the price was last reported |
| `stations` | List of up to 5 cheapest stations with price and updated time |
| `city` | Configured city |
| `fuel_type` | Fuel type label |

### Specific station mode

Tracks a single station's price. Sensor names follow the pattern `sensor.<station_name>_<fuel>`.

| Attribute | Description |
|-----------|-------------|
| `station` | Station name |
| `updated` | When the price was last reported |
| `city` | Configured city |
| `fuel_type` | Fuel type label |

You can add multiple entries — one for cheapest and one or more for specific stations — by going through the setup again.

## Dashboard cards

### Entity Card — single price

The simplest option, no extra integrations required.

```yaml
type: entity
entity: sensor.fuel_price_<city>_95_e10
```

### Mushroom Template Card — cheapest station + price

Requires [Mushroom](https://github.com/piitaya/lovelace-mushroom) (available via HACS). For cheapest mode.

```yaml
type: custom:mushroom-template-card
primary: "{{ state_attr('sensor.fuel_price_<city>_95_e10', 'cheapest_station') }}"
secondary: "{{ states('sensor.fuel_price_<city>_95_e10') }} €/l — {{ state_attr('sensor.fuel_price_<city>_95_e10', 'cheapest_updated') }}"
icon: mdi:gas-station
icon_color: green
tap_action:
  action: more-info
```

### Mushroom Template Card — specific station

For specific station mode.

```yaml
type: custom:mushroom-template-card
primary: "{{ state_attr('sensor.<station>_95_e10', 'station') }}"
secondary: "{{ states('sensor.<station>_95_e10') }} €/l — {{ state_attr('sensor.<station>_95_e10', 'updated') }}"
icon: mdi:gas-station
icon_color: blue
tap_action:
  action: more-info
```

### Markdown Card — top 5 list for one fuel type

For cheapest mode.

```yaml
type: markdown
content: >
  ## ⛽ {{ state_attr('sensor.fuel_price_<city>_95_e10', 'fuel_type') }} — {{ state_attr('sensor.fuel_price_<city>_95_e10', 'city') | capitalize }}

  {% for s in state_attr('sensor.fuel_price_<city>_95_e10', 'stations') %}
  **{{ loop.index }}.** {{ s.station }} — {{ s.price }} €/l *({{ s.updated }})*
  {% endfor %}
```

### Markdown Card — all fuel types combined

For cheapest mode.

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

1. Enter the base URL of a compatible fuel price service and the city name (e.g. `oulu`, `helsinki`, `tampere`)
2. Depending on the source, you may be asked to select a station — choose a specific station to track its price, or select **Cheapest (top 5)** to always show the best available price
3. Select which fuel types to track

You can add multiple entries for the same city by repeating the process — for example one entry in cheapest mode and another tracking a specific station.
