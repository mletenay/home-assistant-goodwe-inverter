"""Support for GoodWe inverter via UDP."""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta
from .goodwe_inverter import discover, InverterError

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    TEMP_CELSIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

CONF_SENSOR_NAME_PREFIX = "sensor_name_prefix"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=8899): cv.port,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(seconds=30)): cv.time_period,
        vol.Optional(CONF_SENSOR_NAME_PREFIX, default="GoodWe"): cv.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    api = await discover(config[CONF_IP_ADDRESS], config[CONF_PORT])
    endpoint = RealTimeDataEndpoint(hass, api)
    resp = await api.get_data()
    serial = resp.serial_number
    hass.async_add_job(endpoint.async_refresh)
    async_track_time_interval(hass, endpoint.async_refresh, config[CONF_SCAN_INTERVAL])
    devices = []
    for (_, idx, _, unit, sensor, icon) in api.sensors():
        if unit == "C":
            unit = TEMP_CELSIUS
        uid = f"goodwe-{serial}-{idx}"
        sensor_name = f"{config[CONF_SENSOR_NAME_PREFIX]} {sensor}".strip()
        devices.append(InverterSensor(uid, sensor, sensor_name, unit, icon))
    endpoint.sensors = devices
    async_add_entities(devices)


class RealTimeDataEndpoint:
    """Representation of a Sensor."""

    def __init__(self, hass, api):
        """Initialize the sensor."""
        self.hass = hass
        self.api = api
        self.ready = asyncio.Event()
        self.sensors = []

    async def async_refresh(self, now=None):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            api_response = await self.api.get_data()
            self.ready.set()
        except InverterError:
            if now is not None:
                self.ready.clear()
                return
            raise PlatformNotReady
        data = api_response.data
        for sensor in self.sensors:
            if sensor.key in data:
                sensor.value = data[sensor.key]
                sensor.async_schedule_update_ha_state()


class InverterSensor(Entity):
    """Class for a sensor."""

    def __init__(self, uid, key, sensor_name, unit, icon_name):
        """Initialize an inverter sensor."""
        self.uid = uid
        self.key = key
        self.sensor_name = sensor_name
        self.value = None
        self.unit = unit
        self.icon_name = icon_name

    @property
    def state(self):
        """State of this inverter attribute."""
        return self.value

    @property
    def unique_id(self):
        """Return unique id."""
        return self.uid

    @property
    def name(self):
        """Name of this inverter attribute."""
        return self.sensor_name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.unit

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self.icon_name

    @property
    def should_poll(self):
        """No polling needed."""
        return False
