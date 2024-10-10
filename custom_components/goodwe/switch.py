"""GoodWe PV inverter switch entities."""

from dataclasses import dataclass
import logging
from typing import Any

from goodwe import Inverter, InverterError
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import BaseCoordinatorEntity

from .coordinator import GoodweUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class GoodweSwitchEntityDescription(SwitchEntityDescription):
    """Class describing Goodwe switch entities."""

    setting: str
    polling_interval: int = 0


SWITCHES = (
    GoodweSwitchEntityDescription(
        key="load_control",
        translation_key="load_control",
        device_class=SwitchDeviceClass.OUTLET,
        setting="load_control_switch",
    ),
    GoodweSwitchEntityDescription(
        key="grid_export_limit_switch",
        translation_key="grid_export_limit_switch",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        setting="grid_export",
    ),
    GoodweSwitchEntityDescription(
        key="fast_charging_switch",
        translation_key="fast_charging_switch",
        device_class=SwitchDeviceClass.SWITCH,
        setting="fast_charging",
        polling_interval=30,
    ),
    GoodweSwitchEntityDescription(
        key="backup_supply_switch",
        translation_key="backup_supply_switch",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        setting="backup_supply",
    ),
    GoodweSwitchEntityDescription(
        key="dod_holding_switch",
        translation_key="dod_holding_switch",
        entity_category=EntityCategory.CONFIG,
        device_class=SwitchDeviceClass.SWITCH,
        setting="dod_holding",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the inverter switch entities from a config entry."""
    inverter = config_entry.runtime_data.inverter
    coordinator = config_entry.runtime_data.coordinator
    device_info = config_entry.runtime_data.device_info

    entities = []

    for description in SWITCHES:
        try:
            current_state = await inverter.read_setting(description.setting)
        except (InverterError, ValueError):
            # Inverter model does not support this feature
            _LOGGER.debug("Could not read %s value", description.setting)
        else:
            entities.append(
                InverterSwitchEntity(
                    coordinator,
                    device_info,
                    description,
                    inverter,
                    current_state == 1,
                )
            )

    async_add_entities(entities)


class InverterSwitchEntity(
    BaseCoordinatorEntity[GoodweUpdateCoordinator], SwitchEntity
):
    """Switch representation of inverter's 'Load Control' relay."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    entity_description: GoodweSwitchEntityDescription

    def __init__(
        self,
        coordinator: GoodweUpdateCoordinator,
        device_info: DeviceInfo,
        description: GoodweSwitchEntityDescription,
        inverter: Inverter,
        current_is_on: bool,
    ) -> None:
        """Initialize the inverter operation mode setting entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_is_on = current_is_on
        self._inverter: Inverter = inverter
        self._notify_coordinator()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._inverter.write_setting(self.entity_description.setting, 1)
        self._attr_is_on = True
        self._notify_coordinator()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._inverter.write_setting(self.entity_description.setting, 0)
        self._attr_is_on = False
        self._notify_coordinator()
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Get the current value from inverter."""
        value = await self._inverter.read_setting(self.entity_description.setting)
        self._attr_is_on = value == 1
        self._notify_coordinator()

    def _notify_coordinator(self) -> None:
        if self.entity_description.polling_interval:
            self.coordinator.entity_state_polling(
                self,
                self.entity_description.polling_interval if self._attr_is_on else 0,
            )
