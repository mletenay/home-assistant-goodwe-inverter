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
from homeassistant.core import callback
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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    KEY_INVERTER,
    KEY_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

# Service related constants
SERVICE_SET_WORK_MODE = "set_work_mode"
ATTR_WORK_MODE = "work_mode"
SET_WORK_MODE_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_WORK_MODE): cv.positive_int,}
)
SERVICE_SET_ONGRID_BATTERY_DOD = "set_ongrid_battery_dod"
ATTR_ONGRID_BATTERY_DOD = "ongrid_battery_dod"
SET_ONGRID_BATTERY_DOD_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ONGRID_BATTERY_DOD): cv.positive_int,}
)
SERVICE_SET_GRID_EXPORT_LIMIT = "set_grid_export_limit"
ATTR_GRID_EXPORT_LIMIT = "grid_export_limit"
SET_GRID_EXPORT_LIMIT_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_GRID_EXPORT_LIMIT): cv.positive_int,}
)

_ICONS = {
    SensorKind.PV: "mdi:solar-power",
    SensorKind.AC: "mdi:power-plug-outline",
    SensorKind.UPS: "mdi:power-plug-off-outline",
    SensorKind.BAT: "mdi:battery-high",
    SensorKind.GRID: "mdi:transmission-tower",
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the GoodWe inverter from a config entry."""
    entities = []
    inverter = hass.data[DOMAIN][config_entry.entry_id][KEY_INVERTER]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]

    # Entity representing inverter itself
    uid = f"{DOMAIN}-{inverter.serial_number}"
    inverter_entity = InverterEntity(coordinator, inverter, uid, config_entry)
    entities.append(inverter_entity)

    # Individual inverter sensors entities
    for sensor in inverter.sensors():
        if sensor.id_.startswith("xx"):
            # do not include unknown sensors
            continue
        uid = f"{DOMAIN}-{sensor.id_}-{inverter.serial_number}"
        sensor_name = f"{DEFAULT_NAME} {sensor.name}".strip()
        entities.append(
            InverterSensor(
                coordinator,
                config_entry,
                uid,
                sensor.id_,
                sensor_name,
                sensor.unit,
                sensor.kind,
            )
        )

    async_add_entities(entities)

    # Add services
    platform = entity_platform.async_get_current_platform()
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


class InverterEntity(CoordinatorEntity, SensorEntity):
    """Entity representing the inverter instance itself"""

    def __init__(self, coordinator, inverter, uid, config_entry):
        super().__init__(coordinator)
        self._attr_icon = "mdi:solar-power"
        self._attr_native_value = None
        self._attr_name = "PV Inverter"

        self._inverter = inverter
        self._config_entry = config_entry
        self._attr_unique_id = uid
        self._sensor = "ppv"
        self._data = {}

    async def read_runtime_data(self):
        """Read runtime data from the inverter"""
        return await self._inverter.read_runtime_data()

    async def set_work_mode(self, work_mode: int):
        """Set the inverter work mode"""
        await self._inverter.set_work_mode(work_mode)

    async def set_ongrid_battery_dod(self, ongrid_battery_dod: int):
        """Set the on-grid battery dod"""
        await self._inverter.set_ongrid_battery_dod(ongrid_battery_dod)

    async def set_grid_export_limit(self, grid_export_limit: int):
        """Set the grid export limit"""
        await self._inverter.set_grid_export_limit(grid_export_limit)

    @callback
    def _handle_coordinator_update(self):
        """Update the entity value from the response received from inverter."""
        self._data = self.coordinator.data
        self._attr_native_value = self._data.get(self._sensor)

        # async_write_ha_state is called in super()._handle_coordinator_update()
        super()._handle_coordinator_update()

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return POWER_WATT

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
            "identifiers": {(DOMAIN, self._config_entry.unique_id)},
            "model": self._inverter.model_name,
            "manufacturer": "GoodWe",
            "sw_version": self._inverter.software_version,
        }


class InverterSensor(CoordinatorEntity, SensorEntity):
    """Class for a sensor."""

    def __init__(
        self, coordinator, config_entry, uid, sensor_id, sensor_name, unit, kind
    ):
        """Initialize an inverter sensor."""
        super().__init__(coordinator)
        if kind is not None:
            self._attr_icon = _ICONS.get(kind)
        self._attr_name = sensor_name
        self._attr_native_value = None
        self._config_entry = config_entry

        self._attr_unique_id = uid
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

    @callback
    def _handle_coordinator_update(self):
        """Update the sensor value from the response received from inverter."""
        prev_value = self._attr_native_value
        self._attr_native_value = self.coordinator.data.get(self._sensor_id)

        # Total increasing sensor should never be set to None
        if (
            self._attr_native_value is None
            and self._attr_state_class == STATE_CLASS_TOTAL_INCREASING
        ):
            self._attr_native_value = prev_value

        # async_write_ha_state is called in super()._handle_coordinator_update()
        super()._handle_coordinator_update()

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_info(self):
        """Return device info."""
        return {
            "name": self.name,
            "identifiers": {(DOMAIN, self._config_entry.unique_id)},
            "model": self._inverter.model_name,
            "manufacturer": "GoodWe",
            "sw_version": self._inverter.software_version,
        }
