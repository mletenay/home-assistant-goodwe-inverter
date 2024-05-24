"""The Goodwe inverter component."""

from goodwe import InverterError, connect
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_KEEP_ALIVE,
    CONF_MODEL_FAMILY,
    CONF_NETWORK_RETRIES,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_NETWORK_RETRIES,
    DEFAULT_NETWORK_TIMEOUT,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_DEVICE_INFO,
    KEY_INVERTER,
    PLATFORMS,
)
from .coordinator import GoodweUpdateCoordinator
from .services import async_setup_services, async_unload_services


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    protocol = entry.options.get(CONF_PROTOCOL, entry.data.get(CONF_PROTOCOL, "UDP"))
    keep_alive = entry.options.get(CONF_KEEP_ALIVE, protocol != "TCP")
    model_family = entry.options.get(CONF_MODEL_FAMILY, entry.data[CONF_MODEL_FAMILY])
    network_retries = entry.options.get(CONF_NETWORK_RETRIES, DEFAULT_NETWORK_RETRIES)
    network_timeout = entry.options.get(CONF_NETWORK_TIMEOUT, DEFAULT_NETWORK_TIMEOUT)

    # Connect to Goodwe inverter
    try:
        inverter = await connect(
            host=host,
            port=502 if protocol == "TCP" else 8899,
            family=model_family,
            comm_addr=0,
            timeout=network_timeout,
            retries=network_retries,
        )
        inverter.set_keep_alive(keep_alive)
    except InverterError as err:
        raise ConfigEntryNotReady from err

    device_info = DeviceInfo(
        configuration_url="https://www.semsportal.com",
        identifiers={(DOMAIN, inverter.serial_number)},
        name=entry.title,
        manufacturer="GoodWe",
        model=inverter.model_name,
        sw_version=f"{inverter.firmware} / {inverter.arm_firmware}",
        hw_version=f"{inverter.serial_number[5:8]} {inverter.serial_number[0:5]}",
    )

    # Create update coordinator
    coordinator = GoodweUpdateCoordinator(hass, entry, inverter)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_INVERTER: inverter,
        KEY_COORDINATOR: coordinator,
        KEY_DEVICE_INFO: device_info,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
