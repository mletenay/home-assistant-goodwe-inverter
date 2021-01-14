[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

## GoodWe solar inverter sensors for Home Assistant

The component retrieves data from GoodWe solar inverter connected to local network and presents them as sensors in Home Assistant.
GoodWe ET, ES and EM families of inverters are supported, other types may work too.

## Configuration

```YAML
sensor:
  - platform: goodwe
    ip_address: 192.168.100.100
    #port: 8899
    #network_timeout: 2
    #network_retries: 3
    #scan_interval: 30
    #sensor_name_prefix: GoodWe
```

The UDP communication is by definition unreliable, so when no response is received by specified time (`network_timeout` config parameter),
the command will be re-tried up to `network_retries` times.  
The default values (2 secs / 3 times) are fine for most cases, but they can be increased to achieve better stability on less reliable networks.

The optional `sensor_name_prefix` config may be used to change the prefix of the individual sensor's default entity names.

### Documentation

Find the full documentation [here](https://github.com/mletenay/home-assistant-goodwe-inverter).
