[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# GoodWe solar inverter sensors for Home Assistant

This [Home Assistant](https://home-assistant.io/) custom component will retrieve data from a GoodWe inverter connected to a local network.
It has been reported to work on GoodWe ET, EH, BT, BH, ES, EM, DT, D-NS, MS, XS and BP families of inverters.
It may work for other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols.

(If you can't communicate with the inverter despite your model is listed above, it is possible you have old ARM firmware version. You should ask manufacturer support to upgrade your ARM firmware (not just inverter firmware) to be able to communicate with the inveter via UDP.)

## Requirements

Your inverter needs to be connected to your local network, as this custom component will utilise the UDP protocol to read data from it. All you need to know is the IP address of the inverter and you are good to go.

## HACS installation

Add this component using HACS by searching for `GoodWe Inverter Solar Sensor (UDP - no cloud)` on the `Integrations` page.
Then just configure it the standard way in Configuration > Integrations > Add Integration.

## Manual installation

Create a directory called `goodwe` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying all files in `/custom_components/goodwe/` folder from this repo into the new `<config directory>/custom_components/goodwe/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── goodwe
│   ├── __init__.py
│   ├── manifest.json
│   ├── sensor.py
│   └── services.yaml
```

## Configuration example

Since v0.9.2 the plugin is installed and configured via standard HA's mechanism - Configuration > Integrations > Add Integration UI.

For releases < v0.9.2, add the following lines to your `configuration.yaml` file:

```YAML
sensor:
  - platform: goodwe
    ip_address: 192.168.100.100
    #network_timeout: 1
    #network_retries: 3
    #scan_interval: 30
    #inverter_type: ET           # One of ET, EH, ES, EM, DT, NS, XS, BP or None to detect inverter type automatically
    #sensor_name_prefix: GoodWe
    #include_unknown_sensors: false
```

The type (and communication protocol) of the inverter can be detected automatically, but it can be explicitly specified via the `inverter_type` parameter to improve startup reliability and performance. Supported values are ET, EH, ES, EM, DT, NS, XS, BP.

The UDP communication is by definition unreliable, so when no response is received by specified time (`network_timeout` config parameter),
the command will be re-tried up to `network_retries` times.
The default values (2 secs / 3 times) are fine for most cases, but they can be increased to achieve better stability on less reliable networks.

The optional `sensor_name_prefix` config may be used to change the prefix of the individual sensor's default entity names.

There are some values pruduced by the inverters whose meaning is not yet fully known. Those sensors are named "xx\*" and will be provided if the `include_unknown_sensors` parameter is set to true.

## Home Assistant Energy Dashboard

The plugin provides several values suitable for the energy dashboard introduced to HA in v2021.8.
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
- https://github.com/home-assistant/core/tree/dev/homeassistant/components/solax
- https://github.com/robbinjanssen/home-assistant-omnik-inverter
