[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mletenay)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![Build Status](https://github.com/mletenay/home-assistant-goodwe-inverter/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mletenay/home-assistant-goodwe-inverter/actions/workflows/hassfest.yaml)
![GitHub Release](https://img.shields.io/github/v/release/mletenay/home-assistant-goodwe-inverter)

## GoodWe solar inverter for Home Assistant (experimental)

Support for Goodwe solar inverters is present as native integration of [Home Assistant](https://www.home-assistant.io/integrations/goodwe/) since its release 2022.2 and is recommended for most users.

This custom component is experimental version with features not (yet) present in standard HA's integration and is intended for users with specific needs and early adopters of new features.
Use at own risk.

### Differences between this HACS and native HA integration

- EMS modes
- Special work modes `Eco charge mode` and `Eco discharge mode` (24/7 with defined power and SoC).
- Network configuration parameters `Scan iterval`, `Network retry attempts`, `Network request timeout`.
- Switch `Export Limit Switch`.
- Switch `Load Control` (for ET+ inverters).
- Switch and SoC/Power inputs for `Fast Charging` functionality.
- `Start inverter` and `Stop inverter` buttons for grid-only inverters.
- Services for getting/setting inverter configuration parameters

### Migration from HACS to HA

If you have been using this custom component and want to migrate to standard HA integration, the migration is straightforward. Just remove the integration from HACS (press Ignore and force uninstall despite the warning the integration is still configured). Afrer restart of Home Assistant, the standard Goodwe integration will start and all your existing settings, entity names, history and statistics should be preserved.

(If you uninstall the integration first, then uninstall HACS component and install integration back again, it will also work, but you will probably loose some history and settings since HA integration uses slightly different default entity names.)

## Home Assistant Energy Dashboard

The integration provides several values suitable for the energy dashboard introduced to HA in v2021.8.
The best supported are the inverters of ET/EH families, where the sensors `meter_e_total_exp`, `meter_e_total_imp`, `e_total`, `e_bat_charge_total` and `e_bat_discharge_total` are the most suitable for the dashboard measurements and statistics.
For the other inverter families, if such sensors are not directly available from the inverter, they can be calculated, see paragraph below.

## EMS modes

The integration exposes inverter's EMS mode and EMS power (limit) settings.
The following list should explain individual modes and their behavior.

* __Auto__
  * _Scenario:_ Self-use.
  * `PBattery = PInv - Pmeter - Ppv` (Discharge/Charge)
  * The battery power is controlled by the meter power when the meter communication is normal.

* __Charge PV__
  * _Scenario:_ Control the battery to keep charging.
  * `PBattery = Xmax + PV` (Charge)
  * Xmax is to allow the power to be taken from the grid, and PV power is preferred. When set to 0, only PV power is used. Charging power will be limited by charging current limit.
  * _Interpretation:_ Charge Battery from PV (high priority) or Grid (low priority); EmsPowerSet = negative ESS ActivePower (if possible because of PV).
  * Grid: low priority, PV: high priority, Battery: Charge Mode, The control object is 'Grid'


* __Discharge PV__
  * _Scenario:_ Control the battery to keep discharging.
  * `PBattery = Xmax` (Discharge)
  * Xmax is the allowable discharge power of the battery. When the power fed into the grid is limited, PV power will be used first.
  * _Interpretation:_ ESS ActivePower = PV power + EmsPowerSet (i.e. battery discharge); useful for surplus feed-to-grid.
  * PV: high priority, Battery: low priority, Grid: Energy Out Mode, The control object is 'Battery'

* __Import AC__
  * _Scenario:_ The inverter is used as a unit for power grid energy scheduling.
  * `PBattery = Xset + PV` (Charge)
  * Xset refers to the power purchased from the power grid. The power purchased from the grid is preferred. If the PV power is too large, the MPPT power will be limited. (grid side load is not considered)
  * _Interpretation:_ Charge Battery from Grid (high priority) or PV (low priority); EmsPowerSet = negative ESS ActivePower; as long as BMS_CHARGE_MAX_CURRENT is > 0, no AC-Power is exported; when BMS_CHARGE_MAX_CURRENT == 0, PV surplus feed in starts!
  * Grid: high priority, PV: low priority, Battery: Charge Mode, The control object is 'Grid'

* __Export AC__
  * _Scenario:_ The inverter is used as a unit for power grid energy scheduling.
  * `PBattery = Xset` (Discharge)
  * Xset is to sell power to the grid. PV power is preferred. When PV energy is insufficient, the battery will discharge. PV power will be limited by x. (grid side load is not considered)
  * _Interpretation:_ EmsPowerSet = positive ESS ActivePower. But PV will be limited, i.e. remaining power is not used to charge battery.
  * PV: high priority, Battery: low priority, Grid: Energy Out Mode, The control object is 'Grid'

* __Conserve__
  * _Scenario:_ Off-grid reservation mode.
  * `PBattery = PV` (Charge)
  * In on-grid mode, the battery is continuously charged, and only PV power (AC Couple model takes 10% of the rated power of the power grid) is used. The battery can only discharge in off-grid mode.

* __Off-Grid__
  * _Scenario:_ Off-Grid Mode.
  * `PBattery = Pbackup - Ppv` (Charge/Discharge)
  * Forced off-grid operation.

* __Battery Standby__
  * _Scenario:_ The inverter is used as a unit for power grid energy scheduling.
  * `PBattery = 0` (Standby)
  * The battery does not charge and discharge

* __Buy Power__
  * _Scenario:_ Regional energy management.
  * `PBattery = PInv - (Pmeter + Xset) - Ppv` (Charge/Discharge)
  * When the meter communication is normal, the power purchased from the power grid is controlled as Xset. When the PV power is too large, the MPPT power will be limited. When the load is too large, the battery will discharge.
  * _Interpretation:_ Control power at the point of common coupling.
  * Grid: high priority, PV: low priority, Battery: Energy In and Out Mode, The control object is 'Grid'

* __Sell Power__
  * _Scenario:_ Regional energy management.
  * `PBattery = PInv - (Pmeter - Xset) - Ppv` (Charge/Discharge)
  * When the communication of electricity meter is normal, the power sold from the power grid is controlled as Xset, PV power is preferred, and the battery discharges when PV energy is insufficient.PV power will be limited by Xset.
  * _Interpretation:_ Control power at the point of common coupling.
  * PV: high priority, Battery: low priority, Grid: Energy Out Mode, The control object is 'Grid'

* __Charge Battery__
  * _Scenario:_ Force the battery to work at set power value.
  * `PBattery = Xset` (Charge)
  * Xset is the charging power of the battery. PV power is preferred. When PV power is insufficient, it will buy power from the power grid. The charging power is also affected by the charging current limit.
  * _Interpretation:_ Charge Battery from PV (high priority) or Grid (low priority); priorities are inverted compared to IMPORT_AC.
  * PV: high priority, Grid: low priority, Battery: Energy In Mode, The control object is 'Battery'

* __Discharge Battery__
  * _Scenario:_ Force the battery to work at set power value.
  * `PBattery = Xset` (Discharge)
  * Xset is the discharge power of the battery, and the battery discharge has priority. If the PV power is too large, MPPT will be limited. Discharge power is also affected by discharge current limit.
  * _Interpretation:_ ???
  * PV: low priority, Battery: high priority, Grid: Energy In Mode, The control object is 'Battery'

* __Stopped__
	* _Scenario:_ System shutdown.
  * Stop working and turn to wait mode


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

  # Sensor for Riemann sum of energy bought (W -> kWh)
  - platform: integration
    source: sensor.energy_buy
    name: energy_buy_sum
    unit_prefix: k
    round: 1
    method: left
  # Sensor for Riemann sum of energy sold (W -> kWh)
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

To test whether the inverter properly responds to UDP request, just execute the `inverter_test.py` script in your python (3.8+) environment.
The `inverter_scan.py` script can be used to discover inverter(s) on your local network.

## References and inspiration

- https://github.com/marcelblijleven/goodwe
- https://www.photovoltaikforum.com/core/attachment/342066-bluetooth-firmware-update-string-storage-de-v002-pdf/
- https://github.com/robbinjanssen/home-assistant-omnik-inverter
