"""GoodWe PV inverter switch entities."""
import logging
from dataclasses import dataclass
from typing import Any

from goodwe import Inverter, InverterError
from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
    SwitchDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, KEY_DEVICE_INFO, KEY_INVERTER

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class GoodweSettingsSwitchEntityDescription(SwitchEntityDescription):
    """Required values when describing Goodwe switch settings."""

    icon_on: str
    icon_off: str
    settings_name: str


LOAD_CONTROL = GoodweSettingsSwitchEntityDescription(
    key="load_control",
    name="Load Control",
    icon_off="mdi:electric-switch",
    icon_on="mdi:electric-switch-closed",
    entity_category=EntityCategory.CONFIG,
    device_class=SwitchDeviceClass.OUTLET,
    settings_name='load_control_switch',
)

EXPORT_LIMIT_CONTROL = GoodweSettingsSwitchEntityDescription(
    key="grid_export",
    name="Grid Export",
    icon_on="mdi:transmission-tower-off",
    icon_off="mdi:transmission-tower-import",
    entity_category=EntityCategory.CONFIG,
    device_class=SwitchDeviceClass.OUTLET,
    settings_name='grid_export',
)

SWITCHES = (
    LOAD_CONTROL,
    EXPORT_LIMIT_CONTROL,
)


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the inverter switch entities from a config entry."""
    inverter = hass.data[DOMAIN][config_entry.entry_id][KEY_INVERTER]
    device_info = hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE_INFO]

    entities = []

    for description in SWITCHES:
        try:
            current_value = await inverter.read_setting(description.settings_name)
        except (InverterError, ValueError):
            # Inverter model does not support this setting
            _LOGGER.debug("Could not read inverter setting %s", description.key, exc_info=True)
            continue

        entities.append(
            InverterSwitchEntity(device_info, description, inverter, current_value == 1)
        )

    if len(entities) > 0:
        async_add_entities(entities)


class InverterSwitchEntity(SwitchEntity):
    """Inverter switch setting entity."""

    entity_description: GoodweSettingsSwitchEntityDescription

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
            self,
            device_info: DeviceInfo,
            description: GoodweSettingsSwitchEntityDescription,
            inverter: Inverter,
            current_state: bool,
    ) -> None:
        """Initialize the inverter switch setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_is_on = current_state
        self._inverter: Inverter = inverter

    @property
    def icon(self):
        """Return the icon to be displayed for the switch."""
        if self._attr_is_on:
            return self.entity_description.icon_on

        return self.entity_description.icon_off

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self._write_setting(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self._write_setting(0)

    async def async_update(self):
        """Update the state of the inverter."""
        current_value = await self._inverter.read_setting(self.entity_description.settings_name)
        self._attr_is_on = current_value == 1

    async def _write_setting(self, value):
        try:
            await self._inverter.write_setting(self.entity_description.settings_name, value)
            self.async_schedule_update_ha_state(force_refresh=True)
        except InverterError as e:
            _LOGGER.error(
                "Error writing setting: %s=%s: %s",
                self.entity_description.settings_name,
                value,
                e,
            )
