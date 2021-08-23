[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## GoodWe solar inverter sensors for Home Assistant

The component retrieves data from GoodWe solar inverter connected to local network and presents them as sensors in Home Assistant.
GoodWe ET, EH, ES, EM, DT, D-NS and XS families of inverters are supported, other types may work too.

## Configuration

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

### Documentation

Find the full documentation [here](https://github.com/mletenay/home-assistant-goodwe-inverter).
