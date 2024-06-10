"""Diagnostics support for Goodwe."""

from __future__ import annotations

from typing import Any

from goodwe import Inverter, InverterError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, KEY_INVERTER


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    inverter: Inverter = hass.data[DOMAIN][config_entry.entry_id][KEY_INVERTER]

    return {
        "config_entry": config_entry.as_dict(),
        "inverter": {
            "model_name": inverter.model_name,
            "rated_power": inverter.rated_power,
            "firmware": inverter.firmware,
            "arm_firmware": inverter.arm_firmware,
            "dsp1_version": inverter.dsp1_version,
            "dsp2_version": inverter.dsp2_version,
            "dsp_svn_version": inverter.dsp_svn_version,
            "arm_version": inverter.arm_version,
            "arm_svn_version": inverter.arm_svn_version,
            "modbus_address": await _read_register(inverter, 45127),
            "modbus_baudrate": await _read_register(inverter, 45132),
            "log_data_enable": await _read_register(inverter, 47005),
            "data_send_interval": await _read_register(inverter, 47006),
            "wifi_or_lan": await _read_register(inverter, 47009),
            "modbus_tcp_wo_internet": await _read_register(inverter, 47017),
            "wifi_modbus_tcp_enable": await _read_register(inverter, 47040),
        },
    }


async def _read_register(inverter: Inverter, register: int) -> Any:
    try:
        return await inverter.read_setting(f"modbus-{register}")
    except InverterError:
        return None
