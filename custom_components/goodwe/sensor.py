"""Support for GoodWe inverter via UDP."""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta
from .goodwe_inverter import discover, InverterError, SensorKind

from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_VOLTAGE,
    TEMP_CELSIUS,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import PlatformNotReady

_LOGGER = logging.getLogger(__name__)

DOMAIN = "goodwe"
ENTITY_ID_FORMAT = "." + DOMAIN + "_{}"
SERVICE_SET_WORK_MODE = "set_work_mode"
ATTR_WORK_MODE = "work_mode"
SET_WORK_MODE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_WORK_MODE): cv.positive_int,
    }
)
SERVICE_SET_ONGRID_BATTERY_DOD = "set_ongrid_battery_dod"
ATTR_ONGRID_BATTERY_DOD = "ongrid_battery_dod"
SET_ONGRID_BATTERY_DOD_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ONGRID_BATTERY_DOD): cv.positive_int,
    }
)

CONF_SENSOR_NAME_PREFIX = "sensor_name_prefix"
CONF_NETWORK_TIMEOUT = "network_timeout"
CONF_NETWORK_RETRIES = "network_retries"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=8899): cv.port,
        vol.Optional(CONF_NETWORK_TIMEOUT, default=2): cv.positive_int,
        vol.Optional(CONF_NETWORK_RETRIES, default=3): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(seconds=30)): cv.time_period,
        vol.Optional(CONF_SENSOR_NAME_PREFIX, default="GoodWe"): cv.string,
    }
)

_ICONS = {
    SensorKind.pv: "mdi:solar-power",
    SensorKind.ac: "mdi:power-plug-outline",
    SensorKind.ups: "mdi:power-plug-off-outline",
    SensorKind.bat: "mdi:battery-high",
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    try:
        inverter = await discover(config[CONF_IP_ADDRESS], config[CONF_PORT], config[CONF_NETWORK_TIMEOUT], config[CONF_NETWORK_RETRIES])
    except InverterError as err:
        raise PlatformNotReady from err

    entity = InverterEntity(inverter, config[CONF_SENSOR_NAME_PREFIX], hass)

    refresh_job = InverterRefreshJob(hass, entity)
    hass.async_add_job(refresh_job.async_refresh)
    async_track_time_interval(
        hass, refresh_job.async_refresh, config[CONF_SCAN_INTERVAL]
    )

    # Add individual inverter sensor entities
    for (sensor_id, _, _, unit, name, kind) in inverter.sensors():
        uid = f"{DOMAIN}-{sensor_id}-{inverter.serial_number}"
        sensor_name = f"{config[CONF_SENSOR_NAME_PREFIX]} {name}".strip()
        refresh_job.sensors.append(
            InverterSensor(uid, sensor_id, sensor_name, unit, kind, hass)
        )
    async_add_entities(refresh_job.sensors)

    # Add entity representing inverter itself
    async_add_entities((entity,))
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_WORK_MODE,
        {vol.Required(ATTR_WORK_MODE): vol.Coerce(int)},
        "set_work_mode",
    )
    platform.async_register_entity_service(
        SERVICE_SET_ONGRID_BATTERY_DOD,
        {vol.Required(ATTR_ONGRID_BATTERY_DOD): vol.Coerce(int)},
        "set_ongrid_battery_dod",
    )

    return True


class InverterRefreshJob:
    """Job for refreshing inverter sensors values"""

    def __init__(self, hass, entity):
        """Initialize the sensors."""
        self.hass = hass
        self.ready = asyncio.Event()
        self.entity = entity
        self.sensors = []

    async def async_refresh(self, now=None):
        """Fetch new state data for the sensors.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            inverter_response = await self.entity.inverter.read_runtime_data()
            self.ready.set()
        except InverterError as ex:
            _LOGGER.warning("Could not retrieve data from inverter: %s", ex)
            inverter_response = {}
            self.ready.clear()

        self.entity.update_value(inverter_response)
        for sensor in self.sensors:
            sensor.update_value(inverter_response)


class InverterEntity(Entity):
    """Entity representing the inverter instance itself"""

    def __init__(self, inverter, name_prefix, hass):
        super().__init__()
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "inverter", hass=hass
        )
        self.inverter = inverter
        self._name_prefix = name_prefix
        self._uuid = f"{DOMAIN}-{inverter.serial_number}"
        self._value = None
        self._sensor = "ppv"
        self._data = {}

    async def set_work_mode(self, work_mode: int):
        """Set the inverter work mode"""
        await self.inverter.set_work_mode(work_mode)

    async def set_ongrid_battery_dod(self, ongrid_battery_dod: int):
        """Set the on grid battery dod"""
        await self.inverter.set_ongrid_battery_dod(ongrid_battery_dod)

    def update_value(self, inverter_response):
        """Update the entity value from the response received from inverter"""
        self._data = inverter_response
        if self._sensor in inverter_response:
            self._value = inverter_response[self._sensor]
        else:
            self._value = None
        self.async_schedule_update_ha_state()

    @property
    def state(self):
        """State of this inverter attribute."""
        return self._value

    @property
    def unique_id(self):
        """Return unique id."""
        return self._uuid

    @property
    def name(self):
        """Name of this inverter attribute."""
        return "PV Inverter"

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "W"

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return "mdi:solar-power"

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def state_attributes(self):
        """Return the inverter state attributes."""
        return self._data

    @property
    def device_state_attributes(self):
        """Return the inverter state attributes."""
        data = {
            "model": self.inverter.model_name,
            "serial_number": self.inverter.serial_number,
            "software_version": self.inverter.software_version,
        }
        return data

    @property
    def device_info(self):
        """Return device info."""
        return {
            "name": self.name,
            "identifiers": {
                (DOMAIN, self.inverter.serial_number),
                (DOMAIN, self.inverter.host, self.inverter.port),
            },
            "model": self.inverter.model_name,
            "manufacturer": "GoodWe",
            "sw_version": self.inverter.software_version,
        }


class InverterSensor(Entity):
    """Class for a sensor."""

    def __init__(self, uid, sensor_id, sensor_name, unit, kind, hass):
        """Initialize an inverter sensor."""
        super().__init__()
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, sensor_id, hass=hass
        )
        self._uid = uid
        self._sensor_id = sensor_id
        self._sensor_name = sensor_name
        self._unit = unit
        if self._unit == "A":
            self._device_class = DEVICE_CLASS_CURRENT
        elif self._unit == "V":
            self._device_class = DEVICE_CLASS_VOLTAGE
        elif self._unit == "W":
            self._device_class = DEVICE_CLASS_POWER
        elif self._unit == "kWh":
            self._device_class = DEVICE_CLASS_ENERGY
        elif self._unit == "%" and kind == SensorKind.bat:
            self._device_class = DEVICE_CLASS_BATTERY
        elif self._unit == "C":
            self._unit = TEMP_CELSIUS
            self._device_class = DEVICE_CLASS_TEMPERATURE
        else:
            self._device_class = None
        if kind is not None:
            self._icon_name = _ICONS[kind]
        else:
            self._icon_name = None
        self._value = None

    def update_value(self, inverter_response):
        """Update the sensor value from the response received from inverter"""
        if self._sensor_id in inverter_response:
            self._value = inverter_response[self._sensor_id]
        else:
            self._value = None
        self.async_schedule_update_ha_state()

    @property
    def state(self):
        """State of this inverter attribute."""
        return self._value

    @property
    def unique_id(self):
        """Return unique id."""
        return self._uid

    @property
    def name(self):
        """Name of this inverter attribute."""
        return self._sensor_name

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._icon_name

    @property
    def should_poll(self):
        """No polling needed."""
        return False
