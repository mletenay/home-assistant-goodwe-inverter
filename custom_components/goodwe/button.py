"""GoodWe PV inverter selection settings entities."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from goodwe import Inverter, InverterError
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import GoodweConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class GoodweButtonEntityDescription(ButtonEntityDescription):
    """Class describing Goodwe button entities."""

    setting: str
    action: Callable[[Inverter], Awaitable[None]]


BUTTONS = (
    GoodweButtonEntityDescription(
        key="synchronize_clock",
        translation_key="synchronize_clock",
        entity_category=EntityCategory.CONFIG,
        setting="time",
        action=lambda inv: inv.write_setting("time", datetime.now()),
    ),
    GoodweButtonEntityDescription(
        key="start_inverter",
        translation_key="start_inverter",
        setting="start",
        action=lambda inv: inv.write_setting("start", 0),
    ),
    GoodweButtonEntityDescription(
        key="stop_inverter",
        translation_key="stop_inverter",
        setting="stop",
        action=lambda inv: inv.write_setting("stop", 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GoodweConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter button entities from a config entry."""
    inverter = config_entry.runtime_data.inverter
    device_info = config_entry.runtime_data.device_info

    entities = []

    for description in BUTTONS:
        try:
            await inverter.read_setting(description.setting)
        except (InverterError, ValueError):
            # Inverter model does not support this feature
            _LOGGER.debug("Could not read %s value", description.setting)
        else:
            entities.append(
                GoodweButtonEntity(
                    device_info,
                    description,
                    inverter,
                )
            )

    async_add_entities(entities)


class GoodweButtonEntity(ButtonEntity):
    """Entity representing the inverter clock synchronization button."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    entity_description: GoodweButtonEntityDescription

    def __init__(
        self,
        device_info: DeviceInfo,
        description: GoodweButtonEntityDescription,
        inverter: Inverter,
    ) -> None:
        """Initialize the inverter operation mode setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._inverter: Inverter = inverter

    async def async_press(self) -> None:
        """Triggers the button press service."""
        await self.entity_description.action(self._inverter)
