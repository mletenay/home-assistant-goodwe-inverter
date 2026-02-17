"""The Goodwe inverter component."""

from goodwe import Inverter, InverterError, connect
from goodwe.const import GOODWE_TCP_PORT, GOODWE_UDP_PORT
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo

from .config_flow import GoodweFlowHandler
from .const import (
    CONF_KEEP_ALIVE,
    CONF_MODBUS_ID,
    CONF_MODEL_FAMILY,
    CONF_NETWORK_RETRIES,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_MODBUS_ID,
    DEFAULT_NETWORK_RETRIES,
    DEFAULT_NETWORK_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import GoodweConfigEntry, GoodweRuntimeData, GoodweUpdateCoordinator
from .services import async_setup_services, async_unload_services


async def async_setup_entry(hass: HomeAssistant, entry: GoodweConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
    protocol = entry.options.get(CONF_PROTOCOL, entry.data.get(CONF_PROTOCOL, "UDP"))
    port = entry.options.get(
        CONF_PORT,
        entry.data.get(
            CONF_PORT, GOODWE_TCP_PORT if protocol == "TCP" else GOODWE_UDP_PORT
        ),
    )
    keep_alive = entry.options.get(CONF_KEEP_ALIVE, False)
    model_family = entry.options.get(CONF_MODEL_FAMILY, entry.data[CONF_MODEL_FAMILY])
    network_retries = entry.options.get(CONF_NETWORK_RETRIES, DEFAULT_NETWORK_RETRIES)
    network_timeout = entry.options.get(CONF_NETWORK_TIMEOUT, DEFAULT_NETWORK_TIMEOUT)
    modbus_id = entry.options.get(CONF_MODBUS_ID, DEFAULT_MODBUS_ID)

    # Connect to Goodwe inverter
    try:
        inverter = await connect(
            host=host,
            port=port,
            family=model_family,
            comm_addr=modbus_id,
            timeout=network_timeout,
            retries=network_retries,
        )
        inverter.set_keep_alive(keep_alive)
    except InverterError as err:
        try:
            inverter = await async_check_port(hass, entry, host)
        except InverterError:
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

    entry.runtime_data = GoodweRuntimeData(
        inverter=inverter,
        coordinator=coordinator,
        device_info=device_info,
    )

    hass.data[DOMAIN][entry.entry_id] = entry.runtime_data

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_setup_services(hass)

    return True


async def async_check_port(
    hass: HomeAssistant, entry: GoodweConfigEntry, host: str
) -> Inverter:
    """Check the communication port of the inverter, it may have changed after a firmware update."""
    inverter, port = await GoodweFlowHandler.async_detect_inverter_port(host=host)
    family = type(inverter).__name__
    hass.config_entries.async_update_entry(
        entry,
        data={
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_MODEL_FAMILY: family,
        },
    )
    return inverter


async def async_unload_entry(
    hass: HomeAssistant, config_entry: GoodweConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

        if not hass.data[DOMAIN]:
            await async_unload_services(hass)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: GoodweConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: GoodweConfigEntry
) -> bool:
    """Migrate old config entries."""

    if config_entry.version > 2:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        # Update from version 1 to version 2 adding the PROTOCOL to the config entry
        host = config_entry.data[CONF_HOST]
        port = config_entry.data.get(
            CONF_PORT,
            config_entry.data.get(
                CONF_PORT,
                (
                    GOODWE_TCP_PORT
                    if config_entry.data.get(CONF_PROTOCOL) == "TCP"
                    else GOODWE_UDP_PORT
                ),
            ),
        )
        if not port:
            try:
                _, port = await GoodweFlowHandler.async_detect_inverter_port(host=host)
            except InverterError as err:
                raise ConfigEntryNotReady from err
        new_data = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_PROTOCOL: config_entry.data.get(CONF_PROTOCOL),
            CONF_KEEP_ALIVE: config_entry.data.get(CONF_KEEP_ALIVE),
            CONF_MODEL_FAMILY: config_entry.data.get(CONF_MODEL_FAMILY),
            CONF_SCAN_INTERVAL: config_entry.data.get(CONF_SCAN_INTERVAL),
            CONF_NETWORK_RETRIES: config_entry.data.get(CONF_NETWORK_RETRIES),
            CONF_NETWORK_TIMEOUT: config_entry.data.get(CONF_NETWORK_TIMEOUT),
            CONF_MODBUS_ID: config_entry.data.get(CONF_MODBUS_ID),
        }
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    return True
