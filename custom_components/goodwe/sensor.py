"""Support for GoodWe inverter via UDP."""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta

from .goodwe.goodwe import connect, InverterError, SensorKind

from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)
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
    ELECTRIC_CURRENT_AMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    TEMP_CELSIUS,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import PlatformNotReady
from homeassistant.util.dt import utc_from_timestamp, utcnow


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
SERVICE_SET_GRID_EXPORT_LIMIT = "set_grid_export_limit"
ATTR_GRID_EXPORT_LIMIT = "grid_export_limit"
SET_GRID_EXPORT_LIMIT_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_GRID_EXPORT_LIMIT): cv.positive_int,
    }
)

CONF_INCLUDE_UNKNOWN_SENSORS = "include_unknown_sensors"
CONF_INVERTER_TYPE = "inverter_type"
CONF_SENSOR_NAME_PREFIX = "sensor_name_prefix"
CONF_NETWORK_TIMEOUT = "network_timeout"
CONF_NETWORK_RETRIES = "network_retries"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=8899): cv.port,
        vol.Optional(CONF_INCLUDE_UNKNOWN_SENSORS, default=False): cv.boolean,
        vol.Optional(CONF_INVERTER_TYPE, default=""): cv.string,
        vol.Optional(CONF_NETWORK_TIMEOUT, default=2): cv.positive_int,
        vol.Optional(CONF_NETWORK_RETRIES, default=3): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(seconds=30)): cv.time_period,
        vol.Optional(CONF_SENSOR_NAME_PREFIX, default="GoodWe"): cv.string,
    }
)

_ICONS = {
    SensorKind.PV: "mdi:solar-power",
    SensorKind.AC: "mdi:power-plug-outline",
    SensorKind.UPS: "mdi:power-plug-off-outline",
    SensorKind.BAT: "mdi:battery-high",
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    try:
        inverter = await connect(
            config[CONF_IP_ADDRESS],
            config[CONF_PORT],
            config[CONF_INVERTER_TYPE],
            config[CONF_NETWORK_TIMEOUT],
            config[CONF_NETWORK_RETRIES],
        )
    except InverterError as err:
        raise PlatformNotReady from err

    entity = InverterEntity(
        inverter,
        config[CONF_SENSOR_NAME_PREFIX],
        config[CONF_INCLUDE_UNKNOWN_SENSORS],
        hass,
    )

    refresh_job = InverterRefreshJob(hass, entity)
    hass.async_add_job(refresh_job.async_refresh)
    async_track_time_interval(
        hass, refresh_job.async_refresh, config[CONF_SCAN_INTERVAL]
    )

    # Add individual inverter sensor entities
    for sensor in inverter.sensors():
        uid = f"{DOMAIN}-{sensor.id_}-{inverter.serial_number}"
        sensor_name = f"{config[CONF_SENSOR_NAME_PREFIX]} {sensor.name}".strip()
        refresh_job.sensors.append(
            InverterSensor(uid, sensor.id_, sensor_name, sensor.unit, sensor.kind, hass)
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
    platform.async_register_entity_service(
        SERVICE_SET_GRID_EXPORT_LIMIT,
        {vol.Required(ATTR_GRID_EXPORT_LIMIT): vol.Coerce(int)},
        "set_grid_export_limit",
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
            inverter_response = await self.entity.read_runtime_data()
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

    def __init__(self, inverter, name_prefix, include_unknown_sensors, hass):
        super().__init__()
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "inverter", hass=hass
        )
        self.inverter = inverter
        self._include_unknown_sensors = include_unknown_sensors
        self._name_prefix = name_prefix
        self._uuid = f"{DOMAIN}-{inverter.serial_number}"
        self._value = None
        self._sensor = "ppv"
        self._data = {}

    async def read_runtime_data(self):
        return await self.inverter.read_runtime_data(self._include_unknown_sensors)

    async def set_work_mode(self, work_mode: int):
        """Set the inverter work mode"""
        await self.inverter.set_work_mode(work_mode)

    async def set_ongrid_battery_dod(self, ongrid_battery_dod: int):
        """Set the on-grid battery dod"""
        await self.inverter.set_ongrid_battery_dod(ongrid_battery_dod)

    async def set_grid_export_limit(self, grid_export_limit: int):
        """Set the grid export limit"""
        await self.inverter.set_grid_export_limit(grid_export_limit)

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


class InverterSensor(SensorEntity):
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
        # self._last_reset = utc_from_timestamp(0)
        if unit == "A":
            self._unit = ELECTRIC_CURRENT_AMPERE
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_CURRENT
        elif unit == "V":
            self._unit = ELECTRIC_POTENTIAL_VOLT
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_VOLTAGE
        elif unit == "W":
            self._unit = unit
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_POWER
        elif unit == "kWh":
            self._unit = unit
            self._attr_state_class = STATE_CLASS_MEASUREMENT  # will be replaced with STATE_CLASS_TOTAL_INCREASING
            self._attr_device_class = DEVICE_CLASS_ENERGY
            self._attr_last_reset = utc_from_timestamp(0)
        elif unit == "%" and kind == SensorKind.BAT:
            self._unit = unit
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_BATTERY
        elif unit == "C":
            self._unit = TEMP_CELSIUS
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_TEMPERATURE
        else:
            self._unit = unit
            self._attr_state_class = None
            self._attr_device_class = None

        if kind is not None:
            self._icon_name = _ICONS[kind]
        else:
            self._icon_name = None
        self._value = None

    def update_value(self, inverter_response):
        """Update the sensor value from the response received from inverter"""
        old_value = self._value
        if self._sensor_id in inverter_response:
            self._value = inverter_response[self._sensor_id]
        else:
            self._value = None
        if (
            self._unit == "kWh"
            and old_value
            and self._value
            and (old_value > self._value)
        ):
            self._attr_last_reset = utcnow()
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
