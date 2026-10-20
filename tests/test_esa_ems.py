"""Tests for EMS mode handling on inverters reporting unknown EMS codes (GoodWe ESA)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from goodwe import InverterError, OperationMode
import pytest

from custom_components.goodwe import number as gw_number, select as gw_select


def _inverter(ems_mode=0, rated_power=125, read_error=None):
    inverter = MagicMock()
    inverter.serial_number = "5125KCI0257L0063"
    inverter.rated_power = rated_power
    inverter.get_operation_modes = AsyncMock(return_value=(OperationMode.GENERAL,))
    inverter.get_operation_mode = AsyncMock(side_effect=ValueError("unsupported"))
    inverter.get_grid_export_limit = AsyncMock(side_effect=ValueError("unsupported"))
    inverter.get_ongrid_battery_dod = AsyncMock(side_effect=ValueError("unsupported"))
    inverter.settings = MagicMock(return_value=())

    async def read_setting(name):
        if name == "ems_mode":
            if read_error:
                raise read_error
            return ems_mode
        if name in ("ems_power_limit", "battery_soc_protection"):
            return 0
        raise ValueError(name)

    inverter.read_setting = AsyncMock(side_effect=read_setting)
    inverter.write_setting = AsyncMock()
    return inverter


def _entry(inverter):
    return SimpleNamespace(
        runtime_data=SimpleNamespace(inverter=inverter, device_info={})
    )


async def _setup_select(inverter):
    added = []
    await gw_select.async_setup_entry(None, _entry(inverter), added.extend)
    return [e for e in added if isinstance(e, gw_select.InverterEMSModeEntity)]


async def test_unknown_ems_code_creates_entity() -> None:
    """ESA reports EMS mode 0, the entity must still be created."""
    entities = await _setup_select(_inverter(ems_mode=0))
    assert len(entities) == 1
    assert entities[0].current_option is None
    assert "stop" in entities[0].options
    assert len(entities[0].options) == 13


@pytest.mark.parametrize(
    ("code", "option"),
    [(1, "auto"), (10, "sell_power"), (12, "discharge_battery"), (255, "stop")],
)
async def test_known_ems_codes(code, option) -> None:
    """Known register values map to options."""
    entities = await _setup_select(_inverter(ems_mode=code))
    assert entities[0].current_option == option


async def test_ems_not_supported() -> None:
    """No entity when the inverter rejects the EMS register."""
    inverter = _inverter(read_error=InverterError("not supported"))
    assert await _setup_select(inverter) == []


async def test_select_and_update() -> None:
    """Selecting writes the raw code; update reads it back."""
    inverter = _inverter(ems_mode=0)
    entity = (await _setup_select(inverter))[0]
    entity.async_write_ha_state = MagicMock()

    await entity.async_select_option("stop")
    inverter.write_setting.assert_awaited_once_with("ems_mode", 255)
    assert entity.current_option == "stop"

    await entity.async_select_option("charge_battery")
    inverter.write_setting.assert_awaited_with("ems_mode", 11)

    inverter.read_setting.side_effect = None
    inverter.read_setting.return_value = 0
    await entity.async_update()
    assert entity.current_option is None


@pytest.mark.parametrize(
    ("rated", "expected"), [(125, 12500), (29900, 29900), (0, 0), (None, 0)]
)
def test_rated_power_w(rated, expected) -> None:
    """Rated power reported in 100 W units is converted to W."""
    assert gw_number._rated_power_w(SimpleNamespace(rated_power=rated)) == expected


async def test_ems_power_limit_max() -> None:
    """EMS power limit max uses rated power in W."""
    added = []
    await gw_number.async_setup_entry(None, _entry(_inverter()), added.extend)
    limit = next(e for e in added if e.entity_description.key == "ems_power_limit")
    assert limit.native_max_value == 25000


async def test_ems_select_polls_and_survives_read_errors() -> None:
    """EMS select is polled; a failed read keeps the last known option."""
    inverter = _inverter(ems_mode=12)
    entity = (await _setup_select(inverter))[0]
    assert entity.should_poll is True

    inverter.read_setting.side_effect = InverterError("timeout")
    await entity.async_update()
    assert entity.current_option == "discharge_battery"


async def test_only_ems_power_limit_number_polls() -> None:
    """EMS power limit is polled, other settings are not."""
    added = []
    await gw_number.async_setup_entry(None, _entry(_inverter()), added.extend)
    by_key = {e.entity_description.key: e for e in added}
    assert by_key["ems_power_limit"].should_poll is True
    assert by_key["battery_soc_protection"].should_poll is False


async def test_number_update_keeps_value_on_error() -> None:
    """A failed read keeps the last known value."""
    inverter = _inverter()
    added = []
    await gw_number.async_setup_entry(None, _entry(inverter), added.extend)
    limit = next(e for e in added if e.entity_description.key == "ems_power_limit")

    inverter.read_setting.side_effect = None
    inverter.read_setting.return_value = 2000
    await limit.async_update()
    assert limit.native_value == 2000

    inverter.read_setting.side_effect = InverterError("timeout")
    await limit.async_update()
    assert limit.native_value == 2000


def _operation_mode_entity(inverter):
    entity = gw_select.InverterOperationModeEntity(
        {}, gw_select.OPERATION_MODE, inverter, ["general", "eco"], "eco", 0, 0
    )
    entity.hass = MagicMock()
    entity.async_write_ha_state = MagicMock()
    return entity


@pytest.fixture
def ems_refresh(monkeypatch):
    """Registry knowing both EMS entities and a mocked async_update_entity."""
    ids = {
        "goodwe-ems_mode-5125KCI0257L0063": "select.esa_ems_mode",
        "goodwe-ems_power_limit-5125KCI0257L0063": "number.esa_ems_power_limit",
    }
    registry = MagicMock()
    registry.async_get_entity_id = MagicMock(
        side_effect=lambda platform, domain, unique_id: ids.get(unique_id)
    )
    monkeypatch.setattr(gw_select.er, "async_get", lambda hass: registry)
    update = AsyncMock()
    monkeypatch.setattr(gw_select, "async_update_entity", update)
    return update


async def test_operation_mode_change_refreshes_ems(ems_refresh) -> None:
    """Changing operation mode re-reads EMS mode and EMS power limit."""
    inverter = _inverter()
    inverter.set_operation_mode = AsyncMock()
    entity = _operation_mode_entity(inverter)

    await entity.async_select_option("general")

    inverter.set_operation_mode.assert_awaited_once()
    updated = [c.args[1] for c in ems_refresh.await_args_list]
    assert updated == ["select.esa_ems_mode", "number.esa_ems_power_limit"]


async def test_failed_operation_mode_change_does_not_refresh(ems_refresh) -> None:
    """No refresh when the inverter rejects the operation mode."""
    inverter = _inverter()
    inverter.set_operation_mode = AsyncMock(side_effect=InverterError("rejected"))
    entity = _operation_mode_entity(inverter)

    await entity.async_select_option("general")

    ems_refresh.assert_not_awaited()
    assert entity.current_option == "eco"


async def test_refresh_ignores_update_errors(ems_refresh) -> None:
    """A failing entity refresh does not break the operation mode change."""
    from homeassistant.exceptions import HomeAssistantError

    ems_refresh.side_effect = [HomeAssistantError("not loaded"), None]
    inverter = _inverter()
    inverter.set_operation_mode = AsyncMock()
    entity = _operation_mode_entity(inverter)

    await entity.async_select_option("general")

    assert entity.current_option == "general"
    assert ems_refresh.await_count == 2
