"""The Goodwe inverter component."""
import logging
from datetime import timedelta
from socket import timeout

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .goodwe.goodwe import connect, InverterError

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
    CONF_COMM_ADDRESS,
    CONF_MODEL_FAMILY,
    CONF_SCAN_INTERVAL,
    KEY_INVERTER,
    KEY_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = entry.title
    host = entry.data[CONF_HOST]
    comm_address = entry.data[CONF_COMM_ADDRESS]
    model_family = entry.data[CONF_MODEL_FAMILY]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Connect to Goodwe inverter
    try:
        inverter = await connect(
            host=host, family=model_family, comm_addr=comm_address,
        )
    except InverterError as err:
        raise ConfigEntryNotReady from err

    async def async_update_data():
        """Fetch data from the inverter."""
        try:
            data = await self._inverter_entity.read_runtime_data()
        except InverterError as ex:
            raise UpdateFailed(ex) from ex

        return data

    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=scan_interval),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_INVERTER: inverter,
        KEY_COORDINATOR: coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
