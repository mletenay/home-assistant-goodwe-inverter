"""Constants for the Goodwe component."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "goodwe"

PLATFORMS = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

DEFAULT_NAME = "GoodWe"
SCAN_INTERVAL = timedelta(seconds=10)
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_NETWORK_RETRIES = 10
DEFAULT_NETWORK_TIMEOUT = 1
DEFAULT_MODBUS_ID = 0

CONF_KEEP_ALIVE = "keep_alive"
CONF_MODEL_FAMILY = "model_family"
CONF_NETWORK_RETRIES = "network_retries"
CONF_NETWORK_TIMEOUT = "network_timeout"
CONF_MODBUS_ID = "modbus_id"

SERVICE_GET_PARAMETER = "get_parameter"
SERVICE_SET_PARAMETER = "set_parameter"
ATTR_DEVICE_ID = "device_id"
ATTR_ENTITY_ID = "entity_id"
ATTR_PARAMETER = "parameter"
ATTR_VALUE = "value"
