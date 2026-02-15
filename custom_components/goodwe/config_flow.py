"""Config flow to configure Goodwe inverters using their local API."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from goodwe import Inverter, InverterError, connect
from goodwe.const import GOODWE_TCP_PORT, GOODWE_UDP_PORT
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_KEEP_ALIVE,
    CONF_MODBUS_ID,
    CONF_MODEL_FAMILY,
    CONF_NETWORK_RETRIES,
    CONF_NETWORK_TIMEOUT,
    DEFAULT_MODBUS_ID,
    DEFAULT_NAME,
    DEFAULT_NETWORK_RETRIES,
    DEFAULT_NETWORK_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

PROTOCOL_CHOICES = ["UDP", "TCP"]
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PROTOCOL, default="UDP"): vol.In(PROTOCOL_CHOICES),
        vol.Required(CONF_MODEL_FAMILY, default="none"): str,
    }
)
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT): int,
        vol.Required(CONF_PROTOCOL): vol.In(PROTOCOL_CHOICES),
        vol.Required(CONF_KEEP_ALIVE): cv.boolean,
        vol.Required(CONF_MODEL_FAMILY): str,
        vol.Optional(CONF_SCAN_INTERVAL): int,
        vol.Optional(CONF_MODBUS_ID): int,
        vol.Optional(CONF_NETWORK_RETRIES): cv.positive_int,
        vol.Optional(CONF_NETWORK_TIMEOUT): cv.positive_int,
    }
)

_LOGGER = logging.getLogger(__name__)


class OptionsFlowHandler(OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Init object."""
        self.entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        host = self.entry.options.get(CONF_HOST, self.entry.data[CONF_HOST])
        port = self.entry.options.get(CONF_PORT, self.entry.data.get(CONF_PORT))
        protocol = self.entry.options.get(
            CONF_PROTOCOL, self.entry.data.get(CONF_PROTOCOL, "UDP")
        )
        keep_alive = self.entry.options.get(CONF_KEEP_ALIVE, False)
        model_family = self.entry.options.get(
            CONF_MODEL_FAMILY, self.entry.data[CONF_MODEL_FAMILY]
        )
        network_retries = self.entry.options.get(
            CONF_NETWORK_RETRIES, DEFAULT_NETWORK_RETRIES
        )
        network_timeout = self.entry.options.get(
            CONF_NETWORK_TIMEOUT, DEFAULT_NETWORK_TIMEOUT
        )
        modbus_id = self.entry.options.get(CONF_MODBUS_ID, DEFAULT_MODBUS_ID)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_PROTOCOL: protocol,
                    CONF_KEEP_ALIVE: keep_alive,
                    CONF_MODEL_FAMILY: model_family,
                    CONF_SCAN_INTERVAL: self.entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_NETWORK_RETRIES: network_retries,
                    CONF_NETWORK_TIMEOUT: network_timeout,
                    CONF_MODBUS_ID: modbus_id,
                },
            ),
        )


class GoodweFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Goodwe config flow."""

    MINOR_VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_handle_successful_connection(
        self,
        inverter: Inverter,
        host: str,
        port: int,
        protocol: str,
    ) -> ConfigFlowResult:
        """Handle a successful connection storing it's values on the entry data."""
        await self.async_set_unique_id(inverter.serial_number)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=DEFAULT_NAME,
            data={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_PROTOCOL: protocol,
                CONF_MODEL_FAMILY: type(inverter).__name__,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            protocol = user_input[CONF_PROTOCOL]
            model_family = user_input[CONF_MODEL_FAMILY]
            port = user_input.get(
                CONF_PORT, GOODWE_UDP_PORT if protocol == "UDP" else GOODWE_TCP_PORT
            )

            try:
                _LOGGER.debug(
                    "Goodwe connecting to %s:%s protocol=%s family=%s",
                    host,
                    port,
                    protocol,
                    model_family,
                )
                inverter = await connect(
                    host=host, port=port, family=model_family, retries=10
                )
            except InverterError:
                errors[CONF_HOST] = "connection_error"
            else:
                return await self.async_handle_successful_connection(
                    inverter, host, port, protocol
                )
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

    @staticmethod
    async def async_detect_inverter_port(
        host: str,
    ) -> tuple[Inverter, int]:
        """Detects the port of the Inverter."""
        port = GOODWE_UDP_PORT
        try:
            inverter = await connect(host=host, port=port, retries=10)
        except InverterError:
            port = GOODWE_TCP_PORT
            inverter = await connect(host=host, port=port, retries=10)
        return inverter, port
