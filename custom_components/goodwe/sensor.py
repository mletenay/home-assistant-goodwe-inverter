"""Support for GoodWe inverter via UDP."""
import asyncio
import logging
import voluptuous as vol
from datetime import timedelta

from goodwe import connect, InverterError, SensorKind

from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
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
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
    TEMP_CELSIUS,
)
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.exceptions import PlatformNotReady


_LOGGER = logging.getLogger(__name__)

DOMAIN = "goodwe"
ENTITY_ID_FORMAT = "." + DOMAIN + "_{}"

# Service related constants
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

# Configuration related constants
CONF_INCLUDE_UNKNOWN_SENSORS = "include_unknown_sensors"
CONF_INVERTER_TYPE = "inverter_type"
CONF_COMM_ADDRESS = "comm_address"
CONF_SENSOR_NAME_PREFIX = "sensor_name_prefix"
CONF_NETWORK_TIMEOUT = "network_timeout"
CONF_NETWORK_RETRIES = "network_retries"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=8899): cv.port,
        vol.Optional(CONF_INCLUDE_UNKNOWN_SENSORS, default=False): cv.boolean,
        vol.Optional(CONF_INVERTER_TYPE): cv.string,
        vol.Optional(CONF_COMM_ADDRESS): cv.positive_int,
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
    SensorKind.GRID: "mdi:transmission-tower",
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Platform setup."""
    try:
        inverter = await connect(
            config[CONF_IP_ADDRESS],
            config.get(CONF_INVERTER_TYPE),
            config.get(CONF_COMM_ADDRESS),
            config[CONF_NETWORK_TIMEOUT],
            config[CONF_NETWORK_RETRIES],
        )
    except InverterError as err:
        raise PlatformNotReady from err

    # Entity representing inverter itself
    entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, "inverter", hass=hass)
    uid = f"{DOMAIN}-{inverter.serial_number}"
    inverter_entity = InverterEntity(inverter, entity_id, uid)
    async_add_entities((inverter_entity,))

    # Individual inverter sensors entities
    sensor_entities = []
    for sensor in inverter.sensors():
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, sensor.id_, hass=hass)
        uid = f"{DOMAIN}-{sensor.id_}-{inverter.serial_number}"
        sensor_name = f"{config[CONF_SENSOR_NAME_PREFIX]} {sensor.name}".strip()
        sensor_entities.append(
            InverterSensor(
                entity_id, uid, sensor.id_, sensor_name, sensor.unit, sensor.kind
            )
        )
    async_add_entities(sensor_entities)

    # Add the refresh job
    refresh_job = InverterValuesRefreshJob(
        inverter_entity,
        sensor_entities,
        config[CONF_NETWORK_RETRIES],
        config[CONF_INCLUDE_UNKNOWN_SENSORS],
    )
    hass.async_add_job(refresh_job.async_refresh)
    async_track_time_interval(
        hass, refresh_job.async_refresh, config[CONF_SCAN_INTERVAL]
    )

    # Add services
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


class InverterValuesRefreshJob:
    """Job for refreshing inverter sensors values"""

    def __init__(
        self, inverter_entity, sensor_entities, network_retries, include_unknown_sensors
    ):
        """Initialize the sensors."""
        self._inverter_entity = inverter_entity
        self._sensor_entities = sensor_entities
        self._network_retries = network_retries
        self._include_unknown_sensors = include_unknown_sensors
        self._network_failure_count = 0

    async def async_refresh(self, now=None):
        """Fetch new state data for the sensors.

        This is the only method that should fetch new data for Home Assistant.
        """
        try:
            inverter_response = await self._inverter_entity.read_runtime_data(
                self._include_unknown_sensors
            )
            self._network_failure_count = 0
        except InverterError as ex:
            self._network_failure_count += 1
            if self._network_failure_count > self._network_retries:
                _LOGGER.debug("Inverter is not responding to requests: %s", ex)
                inverter_response = {}
            else:
                return

        self._inverter_entity.update_value(inverter_response)
        for sensor in self._sensor_entities:
            sensor.update_value(inverter_response)


class InverterEntity(SensorEntity):
    """Entity representing the inverter instance itself"""

    def __init__(self, inverter, entity_id, uid):
        super().__init__()
        self.entity_id = entity_id
        self._attr_icon = "mdi:solar-power"
        self._attr_native_value = None
        self._attr_name = "PV Inverter"

        self._inverter = inverter
        self._uid = uid
        self._sensor = "ppv"
        self._data = {}

    async def read_runtime_data(self, include_unknown_sensors):
        """Read runtime data from the inverter"""
        return await self._inverter.read_runtime_data(include_unknown_sensors)

    async def set_work_mode(self, work_mode: int):
        """Set the inverter work mode"""
        await self._inverter.set_work_mode(work_mode)

    async def set_ongrid_battery_dod(self, ongrid_battery_dod: int):
        """Set the on-grid battery dod"""
        await self._inverter.set_ongrid_battery_dod(ongrid_battery_dod)

    async def set_grid_export_limit(self, grid_export_limit: int):
        """Set the grid export limit"""
        await self._inverter.set_grid_export_limit(grid_export_limit)

    def update_value(self, inverter_response):
        """Update the entity value from the response received from inverter"""
        self._data = inverter_response
        self._attr_native_value = inverter_response.get(self._sensor)
        self.async_schedule_update_ha_state()

    @property
    def unique_id(self):
        """Return unique id."""
        return self._uid

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return POWER_WATT

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def state_attributes(self):
        """Return the inverter state attributes."""
        return self._data

    @property
    def extra_state_attributes(self):
        """Return the inverter state attributes."""
        data = {
            "model": self._inverter.model_name,
            "serial_number": self._inverter.serial_number,
            "software_version": self._inverter.software_version,
        }
        return data

    @property
    def device_info(self):
        """Return device info."""
        return {
            "name": self.name,
            "identifiers": {
                (DOMAIN, self._inverter.serial_number),
                (DOMAIN, self._inverter.host),
            },
            "model": self._inverter.model_name,
            "manufacturer": "GoodWe",
            "sw_version": self._inverter.software_version,
        }


class InverterSensor(SensorEntity):
    """Class for a sensor."""

    def __init__(self, entity_id, uid, sensor_id, sensor_name, unit, kind):
        """Initialize an inverter sensor."""
        super().__init__()
        self.entity_id = entity_id
        if kind is not None:
            self._attr_icon = _ICONS.get(kind)
        self._attr_name = sensor_name
        self._attr_native_value = None

        self._uid = uid
        self._sensor_id = sensor_id
        if unit == "A":
            self._unit = ELECTRIC_CURRENT_AMPERE
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_CURRENT
        elif unit == "V":
            self._unit = ELECTRIC_POTENTIAL_VOLT
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_VOLTAGE
        elif unit == "W":
            self._unit = POWER_WATT
            self._attr_state_class = STATE_CLASS_MEASUREMENT
            self._attr_device_class = DEVICE_CLASS_POWER
        elif unit == "kWh":
            self._unit = ENERGY_KILO_WATT_HOUR
            self._attr_state_class = STATE_CLASS_TOTAL_INCREASING
            self._attr_device_class = DEVICE_CLASS_ENERGY
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

    def update_value(self, inverter_response):
        """Update the sensor value from the response received from inverter"""
        prev_value = self._attr_native_value
        self._attr_native_value = inverter_response.get(self._sensor_id)
        # Total increasing sensor should never be set to None
        if (
            self._attr_native_value is None
            and self._attr_state_class == STATE_CLASS_TOTAL_INCREASING
        ):
            self._attr_native_value = prev_value
        # do not update sensor state if the value hasn't changed
        if self._attr_native_value != prev_value:
            self.async_schedule_update_ha_state()

    @property
    def unique_id(self):
        """Return unique id."""
        return self._uid

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def should_poll(self):
        """No polling needed."""
        return False
