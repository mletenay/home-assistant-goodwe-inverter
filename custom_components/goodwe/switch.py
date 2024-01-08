"""GoodWe PV inverter switch entities."""
import logging
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

LOAD_CONTROL = SwitchEntityDescription(
    key="load_control",
    name="Load Control",
    icon="mdi:electric-switch",
    entity_category=EntityCategory.CONFIG,
    device_class=SwitchDeviceClass.OUTLET,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the inverter switch entities from a config entry."""
    inverter = hass.data[DOMAIN][config_entry.entry_id][KEY_INVERTER]
    device_info = hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE_INFO]

    # read current load control state from the inverter
    try:
        current_state = await inverter.read_setting("load_control_switch")
    except (InverterError, ValueError):
        # Inverter model does not support this feature
        _LOGGER.debug("Could not read load control switch value", exc_info=True)
    else:
        entity = LoadControlSwitch(
            device_info,
            LOAD_CONTROL,
            inverter,
            current_state == 1,
        )
        async_add_entities([entity])


class LoadControlSwitch(SwitchEntity):
    """Switch representation of inverter's 'Load Control' relay."""

    _attr_should_poll = False

    def __init__(
        self,
        device_info: DeviceInfo,
        description: SwitchEntityDescription,
        inverter: Inverter,
        current_is_on: bool,
    ) -> None:
        """Initialize the inverter operation mode setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_is_on = current_is_on
        self._inverter: Inverter = inverter

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._inverter.write_setting("load_control_switch", 1)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._inverter.write_setting("load_control_switch", 0)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Process update from entity."""
        status = await self._inverter.read_setting("load_control_switch")
        return status == 1
