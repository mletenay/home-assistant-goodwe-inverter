[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# GoodWe solar inverter sensors for Home Assistant

The GoodWe Inverter Solar Sensor component will retrieve data from a GoodWe inverter connected to local network.
It has been tested on GoodWe ET, EH, ES, EM, DT, D-NS and XS families of inverters.
It may work for other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols.

The values will be presented as sensors in [Home Assistant](https://home-assistant.io/).

## Requirements

Your inverter needs to be connected to your local network, as this custom component will utilise the UDP protocol to read data from inverter. All you need to know is the IP address of the inverter and you are good to go.

## HACS installation

Add this component using HACS by searching for `GoodWe Inverter Solar Sensor (UDP - no cloud)` on the `Integrations` page.

## Manual installation

Create a directory called `goodwe` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying all files in `/custom_components/goodwe/` folder from this repo into the new `<config directory>/custom_components/goodwe/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── goodwe
│   ├── __init__.py
│   ├── goodwe_inverter.py
│   ├── manifest.json
│   └── sensor.py
```

## Configuration example

To enable this sensor, add the following lines to your `configuration.yaml` file:

```YAML
sensor:
  - platform: goodwe
    ip_address: 192.168.100.100
    #port: 8899
    #network_timeout: 2
    #network_retries: 3
    #scan_interval: 30
    #inverter_type: ET           # One of ET, EH, ES, EM, DT, NS, XS or None to detect inverter type automatically
    #sensor_name_prefix: GoodWe
    #include_unknown_sensors: false
```

The type (and communication protocol) of inverter can be detected automatically, but it is generally recommended to explicitly specify the `inverter_type` to improve startup reliability and performance. One of ET, EH, ES, EM, DT, NS, XS can be specified.

The UDP communication is by definition unreliable, so when no response is received by specified time (`network_timeout` config parameter),
the command will be re-tried up to `network_retries` times.
The default values (2 secs / 3 times) are fine for most cases, but they can be increased to achieve better stability on less reliable networks.

The optional `sensor_name_prefix` config may be used to change the prefix of the individual sensor's default entity names.

There are many values reported by the inverers whose meaning is not yet fully known. Those sensors are named "xx\*" and will be provided if the `include_unknown_sensors` parameter is set to true.

## Cumulative energy values

The sensor values reported by the inverter are instant measurements.
To report summary values like daily/monthly sell or buy (in kWh), these values have to be aggregated over time.
(The only exception are the "total/daily" sensors like `e_total`, `e_day` where the inverter itselfs keeps intenal counters.)

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

## Inverter discovery and communication testing

To test whether the inverter properly responds to UDP request, just execute the `inverter_test.py` script in your python (3.7+) environment.
The `inverter_scan.py` script can be used to discover inverter(s) on your local network.

## References and inspiration

- https://github.com/marcelblijleven/goodwe
- https://github.com/home-assistant/core/tree/dev/homeassistant/components/solax
- https://github.com/robbinjanssen/home-assistant-omnik-inverter
