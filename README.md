[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Build Status](https://github.com/mletenay/home-assistant-goodwe-inverter/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mletenay/home-assistant-goodwe-inverter/actions/workflows/hassfest.yaml)

## GoodWe solar inverter for Home Assistant (experimental)

Support for Goodwe solar inverters is present as native integration of [Home Assistant](https://www.home-assistant.io/integrations/goodwe/) since its release 2022.2 and is recommended for most users.

This custom component is experimental version with features not (yet) present in standard HA's integration and is intended for users with specific needs and early adopters of new features.
Use at own risk.

### Differences between HACS 0.9.9.9 and HA 2023.10

- Integration configuration parameters `Scan iterval`, `Network retry attempts`, `Network request timeout`.
- Special work modes `Eco charge mode` and `Eco discharge mode` (24/7 with defined power and SoC).
- Switch `Load Control` (for ET+ inverters).
- Services for getting/setting inverter configuration parameters

### Migration from HACS to HA

If you have been using this custom component and want to migrate to standard HA integration, the migration is straightforward. Just remove the integration from HACS (press Ignore and force uninstall despite the warning the integration is still configured). Atrer restart of Home Assistant, the standard Goodwe integration will start and all your existing settings, entity names, history and statistics should be preserved.

(If you uninstall the integration first, then uninstall HACS component and install integration back again, it will also work, but you will probably loose some history and settings since HA integration uses slightly different default entity names.)

## Home Assistant Energy Dashboard

The integration provides several values suitable for the energy dashboard introduced to HA in v2021.8.
The best supported are the inverters of ET/EH families, where the sensors `meter_e_total_exp`, `meter_e_total_imp`, `e_total`, `e_bat_charge_total` and `e_bat_discharge_total` are the most suitable for the dashboard measurements and statistics.
For the other inverter families, if such sensors are not directly available from the inverter, they can be calculated, see paragraph below.

## Cumulative energy values

The sensor values reported by the inverter are instant measurements.
To report summary (energy) values like daily/monthly sell or buy (in kWh), these values have to be aggregated over time.

[Riemann Sum](https://www.home-assistant.io/integrations/integration/) integration can be used to convert these instant (W) values into cumulative values (Wh).
[Utility Meter](https://www.home-assistant.io/integrations/utility_meter) can report these values as human readable statistical values.
[Template Sensor](https://www.home-assistant.io/integrations/template/) can be used to separate buy and sell values.

```YAML
sensor:
  - platform: template
    sensors:
      # Template sensor for values of energy bought (active_power < 0)
      energy_buy:
        device_class: power
        friendly_name: "Energy Buy"
        unit_of_measurement: 'W'
        value_template: >-
          {% if states('sensor.goodwe_active_power')|float < 0 %}
            {{ states('sensor.goodwe_active_power')|float * -1 }}
          {% else %}
            {{ 0 }}
          {% endif %}
      # Template sensor for values of energy sold (active_power > 0)
      energy_sell:
        device_class: power
        friendly_name: "Energy Sell"
        unit_of_measurement: 'W'
        value_template: >-
          {% if states('sensor.goodwe_active_power')|float > 0 %}
            {{ states('sensor.goodwe_active_power')|float }}
          {% else %}
            {{ 0 }}
          {% endif %}

  # Sensor for Riemann sum of energy bought (W -> Wh)
  - platform: integration
    source: sensor.energy_buy
    name: energy_buy_sum
    unit_prefix: k
    round: 1
    method: left
  # Sensor for Riemann sum of energy sold (W -> Wh)
  - platform: integration
    source: sensor.energy_sell
    name: energy_sell_sum
    unit_prefix: k
    round: 1
    method: left

utility_meter:
  energy_buy_daily:
    source: sensor.energy_buy_sum
    cycle: daily
  energy_buy_monthly:
    source: sensor.energy_buy_sum
    cycle: monthly
  energy_sell_daily:
    source: sensor.energy_sell_sum
    cycle: daily
  energy_sell_monthly:
    source: sensor.energy_sell_sum
    cycle: monthly
  house_consumption_daily:
    source: sensor.house_consumption_sum
    cycle: daily
  house_consumption_monthly:
    source: sensor.house_consumption_sum
    cycle: monthly
```

## Troubleshooting

If you observe any problems or cannot make it work with your inverter at all, try to increase logging level of the component and check the log files.

```YAML
logger:
  default: warning
  logs:
    custom_components.goodwe: debug
    goodwe: debug
```

## Source code

The source code implementing the actual communication with GoodWe inverters (which was originally part of this plugin) was extracted and moved to standalone [PyPI library](https://pypi.org/project/goodwe/). This repository now contains only the HomeAssistant specific code.

## Inverter discovery and communication testing

To test whether the inverter properly responds to UDP request, just execute the `inverter_test.py` script in your python (3.7+) environment.
The `inverter_scan.py` script can be used to discover inverter(s) on your local network.

## References and inspiration

- https://github.com/marcelblijleven/goodwe
- https://www.photovoltaikforum.com/core/attachment/342066-bluetooth-firmware-update-string-storage-de-v002-pdf/
- https://github.com/robbinjanssen/home-assistant-omnik-inverter
