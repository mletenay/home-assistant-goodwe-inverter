"""GoodWe PV inverter numeric settings entities."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging

from goodwe import Inverter, InverterError
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import GoodweConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class GoodweNumberEntityDescription(NumberEntityDescription):
    """Class describing Goodwe number entities."""

    getter: Callable[[Inverter], Awaitable[any]]
    mapper: Callable[[any], int]
    setter: Callable[[Inverter, int], Awaitable[None]]
    filter: Callable[[Inverter], bool]


def _get_setting_unit(inverter: Inverter, setting: str) -> str:
    """Return the unit of an inverter setting."""
    return next((s.unit for s in inverter.settings() if s.id_ == setting), "")


async def set_offline_battery_dod(inverter: Inverter, dod: int) -> None:
    """Sets offline battery dod - dod for backup output."""
    if 10 <= dod <= 100:
        await inverter.write_setting("battery_discharge_depth_offline", 100 - dod)


async def get_offline_battery_dod(inverter: Inverter) -> int:
    """Returns offline battery dod - dod for backup output."""
    return 100 - (await inverter.read_setting("battery_discharge_depth_offline"))


NUMBERS = (
    # Only one of the export limits are added.
    # Availability is checked in the filter method.
    # Export limit in W
    GoodweNumberEntityDescription(
        key="grid_export_limit",
        translation_key="grid_export_limit",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_step=100,
        native_min_value=0,
        getter=lambda inv: inv.get_grid_export_limit(),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.set_grid_export_limit(val),
        filter=lambda inv: _get_setting_unit(inv, "grid_export_limit") != "%",
    ),
    # Export limit in %
    GoodweNumberEntityDescription(
        key="grid_export_limit",
        translation_key="grid_export_limit",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=200,
        getter=lambda inv: inv.get_grid_export_limit(),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.set_grid_export_limit(val),
        filter=lambda inv: _get_setting_unit(inv, "grid_export_limit") == "%",
    ),
    GoodweNumberEntityDescription(
        key="battery_discharge_depth",
        translation_key="battery_discharge_depth",
        icon="mdi:battery-arrow-down",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=99,
        getter=lambda inv: inv.get_ongrid_battery_dod(),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.set_ongrid_battery_dod(val),
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="soc_upper_limit",
        translation_key="soc_upper_limit",
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=100,
        getter=lambda inv: inv.read_setting("soc_upper_limit"),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.write_setting("soc_upper_limit", val),
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="battery_discharge_depth_offline",
        translation_key="battery_discharge_depth_offline",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=99,
        getter=lambda inv: get_offline_battery_dod(inv),
        mapper=lambda v: v,
        setter=lambda inv, val: set_offline_battery_dod(inv, val),
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="eco_mode_power",
        translation_key="eco_mode_power",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=100,
        getter=lambda inv: inv.read_setting("eco_mode_1"),
        mapper=lambda v: abs(v.get_power()) if v.get_power() else 0,
        setter=None,
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="eco_mode_soc",
        translation_key="eco_mode_soc",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=100,
        getter=lambda inv: inv.read_setting("eco_mode_1"),
        mapper=lambda v: v.soc or 0,
        setter=None,
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="fast_charging_power",
        translation_key="fast_charging_power",
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=100,
        getter=lambda inv: inv.read_setting("fast_charging_power"),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.write_setting("fast_charging_power", val),
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="fast_charging_soc",
        translation_key="fast_charging_soc",
        native_unit_of_measurement=PERCENTAGE,
        native_step=1,
        native_min_value=0,
        native_max_value=100,
        getter=lambda inv: inv.read_setting("fast_charging_soc"),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.write_setting("fast_charging_soc", val),
        filter=lambda inv: True,
    ),
    GoodweNumberEntityDescription(
        key="ems_power_limit",
        translation_key="ems_power_limit",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_step=100,
        native_min_value=0,
        getter=lambda inv: inv.read_setting("ems_power_limit"),
        mapper=lambda v: v,
        setter=lambda inv, val: inv.write_setting("ems_power_limit", val),
        filter=lambda inv: True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GoodweConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter select entities from a config entry."""
    inverter = config_entry.runtime_data.inverter
    device_info = config_entry.runtime_data.device_info

    entities = []

    for description in filter(lambda dsc: dsc.filter(inverter), NUMBERS):
        try:
            current_value = description.mapper(await description.getter(inverter))
        except (InverterError, ValueError):
            # Inverter model does not support this setting
            _LOGGER.debug("Could not read inverter setting %s", description.key)
            continue

        entity = InverterNumberEntity(device_info, description, inverter, current_value)
        # Set the max value of grid_export_limit and ems_power_limit (W version)
        if (
            description.key in ("grid_export_limit", "ems_power_limit")
            and description.native_unit_of_measurement == UnitOfPower.WATT
        ):
            entity.native_max_value = (
                inverter.rated_power * 2 if inverter.rated_power else 10000
            )
        entities.append(entity)

    async_add_entities(entities)


class InverterNumberEntity(NumberEntity):
    """Inverter numeric setting entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    entity_description: GoodweNumberEntityDescription

    def __init__(
        self,
        device_info: DeviceInfo,
        description: GoodweNumberEntityDescription,
        inverter: Inverter,
        current_value: int,
    ) -> None:
        """Initialize the number inverter setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_native_value = float(current_value)
        self._inverter: Inverter = inverter

    async def async_update(self) -> None:
        """Get the current value from inverter."""
        value = await self.entity_description.getter(self._inverter)
        self._attr_native_value = float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value to inverter."""
        if self.entity_description.setter:
            await self.entity_description.setter(self._inverter, int(value))
        self._attr_native_value = value
        self.async_write_ha_state()
