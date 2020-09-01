## GoodWe Inverter Sensor Component for Home Assistant.

The GoodWe solar sensor component will retrieve data from an GoodWe solar inverter.
The values will be presented as sensors (or attributes of sensors) in Home Assistant.

## Configuration

``` YAML
sensor:
  - platform: goodwe
    ip_address: 192.168.100.100
    #port: 8899
    #scan_interval: 30
    #sensor_name_prefix: GoodWe
```

### Documentation

Find the full documentation [here](https://github.com/mletenay/home-assistant-goodwe-inverter).