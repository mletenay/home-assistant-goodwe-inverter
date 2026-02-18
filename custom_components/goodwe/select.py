"""GoodWe PV inverter selection settings entities."""

from dataclasses import dataclass
import logging

from goodwe import Inverter, InverterError, OperationMode
from goodwe.inverter import EMSMode
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    EntityCategory,
    Platform,
)
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN
from .coordinator import GoodweConfigEntry

_LOGGER = logging.getLogger(__name__)


_MODE_TO_OPTION: dict[OperationMode, str] = {
    OperationMode.GENERAL: "general",
    OperationMode.OFF_GRID: "off_grid",
    OperationMode.BACKUP: "backup",
    OperationMode.ECO: "eco",
    OperationMode.PEAK_SHAVING: "peak_shaving",
    OperationMode.SELF_USE: "self_use",
    OperationMode.ECO_CHARGE: "eco_charge",
    OperationMode.ECO_DISCHARGE: "eco_discharge",
}

_OPTION_TO_MODE: dict[str, OperationMode] = {
    value: key for key, value in _MODE_TO_OPTION.items()
}


@dataclass(frozen=True, kw_only=True)
class GoodweSelectEntityDescription(SelectEntityDescription):
    """Class describing Goodwe number entities."""

    options: dict[str, EMSMode]


OPERATION_MODE = SelectEntityDescription(
    key="operation_mode",
    entity_category=EntityCategory.CONFIG,
    translation_key="operation_mode",
)

EMS_MODE = GoodweSelectEntityDescription(
    key="ems_mode",
    entity_category=EntityCategory.CONFIG,
    translation_key="ems_mode",
    options={e.name.lower(): e for e in list(EMSMode)},
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GoodweConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter select entities from a config entry."""
    inverter = config_entry.runtime_data.inverter
    device_info = config_entry.runtime_data.device_info

    supported_modes = await inverter.get_operation_modes(True)
    # read current operating mode from the inverter
    try:
        active_mode = await inverter.get_operation_mode()
        eco_mode = await inverter.read_setting("eco_mode_1")
        current_eco_power = abs(eco_mode.power) if eco_mode.power else 0
        current_eco_soc = eco_mode.soc or 0
    except (InverterError, ValueError):
        # Inverter model does not support this setting
        _LOGGER.debug("Could not read inverter operation mode", exc_info=True)
    else:
        active_mode_option = _MODE_TO_OPTION.get(active_mode)
        if active_mode_option is not None:
            entity = InverterOperationModeEntity(
                device_info,
                OPERATION_MODE,
                inverter,
                [v for k, v in _MODE_TO_OPTION.items() if k in supported_modes],
                active_mode_option,
                current_eco_power,
                current_eco_soc,
            )
            async_add_entities([entity])
        else:
            _LOGGER.warning(
                "Active mode %s not found in Goodwe Inverter Operation Mode Entity. Skipping entity creation",
                active_mode,
            )

        eco_mode_power_entity_id = er.async_get(hass).async_get_entity_id(
            Platform.NUMBER,
            DOMAIN,
            f"{DOMAIN}-eco_mode_power-{inverter.serial_number}",
        )
        if eco_mode_power_entity_id:
            async_track_state_change_event(
                hass,
                eco_mode_power_entity_id,
                entity.update_eco_mode_power,
            )
        eco_mode_soc_entity_id = er.async_get(hass).async_get_entity_id(
            Platform.NUMBER,
            DOMAIN,
            f"{DOMAIN}-eco_mode_soc-{inverter.serial_number}",
        )
        if eco_mode_soc_entity_id:
            async_track_state_change_event(
                hass,
                eco_mode_soc_entity_id,
                entity.update_eco_mode_soc,
            )

    # read current EMS mode from the inverter
    try:
        ems_mode = await inverter.get_ems_mode()
    except (InverterError, ValueError):
        # Inverter model does not support EMS modes
        _LOGGER.debug("Could not read inverter EMS mode", exc_info=True)
    else:
        entity = InverterEMSModeEntity(
            device_info,
            EMS_MODE,
            inverter,
            ems_mode,
        )
        async_add_entities([entity])


class InverterOperationModeEntity(SelectEntity):
    """Entity representing the inverter operation mode."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        device_info: DeviceInfo,
        description: SelectEntityDescription,
        inverter: Inverter,
        supported_options: list[str],
        current_mode: str,
        current_eco_power: int,
        current_eco_soc: int,
    ) -> None:
        """Initialize the inverter operation mode setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_options = supported_options
        self._attr_current_option = current_mode
        self._inverter: Inverter = inverter
        self._eco_mode_power = current_eco_power
        self._eco_mode_soc = current_eco_soc

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(
            "Setting operation mode to %s, power %d, max SoC %d",
            option,
            self._eco_mode_power,
            self._eco_mode_soc,
        )
        await self._inverter.set_operation_mode(
            _OPTION_TO_MODE[option], self._eco_mode_power, self._eco_mode_soc
        )
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Get the current value from inverter."""
        value = await self._inverter.get_operation_mode()
        self._attr_current_option = _MODE_TO_OPTION[value]

    async def update_eco_mode_power(self, event: Event) -> None:
        """Update eco mode power value in inverter (when in eco mode)."""
        state = event.data.get("new_state")
        if state is None or state.state in (STATE_UNKNOWN, "", STATE_UNAVAILABLE):
            return

        self._eco_mode_power = int(float(state.state))
        if event.data.get("old_state"):
            operation_mode = _OPTION_TO_MODE[self.current_option]
            if operation_mode in (
                OperationMode.ECO_CHARGE,
                OperationMode.ECO_DISCHARGE,
            ):
                _LOGGER.debug("Setting eco mode power to %d", self._eco_mode_power)
                await self._inverter.set_operation_mode(
                    operation_mode, self._eco_mode_power, self._eco_mode_soc
                )

    async def update_eco_mode_soc(self, event: Event) -> None:
        """Update eco mode SoC value in inverter (when in eco mode)."""
        state = event.data.get("new_state")
        if state is None or state.state in (STATE_UNKNOWN, "", STATE_UNAVAILABLE):
            return

        self._eco_mode_soc = int(float(state.state))
        if event.data.get("old_state"):
            operation_mode = _OPTION_TO_MODE[self.current_option]
            if operation_mode in (
                OperationMode.ECO_CHARGE,
                OperationMode.ECO_DISCHARGE,
            ):
                _LOGGER.debug("Setting eco mode SoC to %d", self._eco_mode_soc)
                await self._inverter.set_operation_mode(
                    operation_mode, self._eco_mode_power, self._eco_mode_soc
                )


class InverterEMSModeEntity(SelectEntity):
    """Entity representing the inverter EMS mode."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    entity_description: GoodweSelectEntityDescription

    def __init__(
        self,
        device_info: DeviceInfo,
        description: GoodweSelectEntityDescription,
        inverter: Inverter,
        current_mode: EMSMode,
    ) -> None:
        """Initialize the inverter operation mode setting entity."""
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}-{description.key}-{inverter.serial_number}"
        self._attr_device_info = device_info
        self._attr_options = list(description.options.keys())
        self._attr_current_option = current_mode.name.lower()
        self._inverter: Inverter = inverter

    async def async_select_option(self, option: str) -> None:
        """Change the EMS mode."""
        _LOGGER.debug("Setting EMS mode to %s")
        await self._inverter.set_ems_mode(self.entity_description.options[option])
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Get the current EMS mode from inverter."""
        value = await self._inverter.get_ems_mode()
        self._attr_current_option = value.name.lower()
