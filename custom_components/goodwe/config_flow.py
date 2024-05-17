"""Config flow to configure Goodwe inverters using their local API."""

from __future__ import annotations

import logging

import voluptuous as vol

from goodwe import InverterError, connect
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PROTOCOL, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_KEEP_ALIVE,
    CONF_MODEL_FAMILY,
    CONF_NETWORK_RETRIES,
    CONF_NETWORK_TIMEOUT,
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
        vol.Required(CONF_PROTOCOL): vol.In(PROTOCOL_CHOICES),
        vol.Required(CONF_KEEP_ALIVE): cv.boolean,
        vol.Required(CONF_MODEL_FAMILY): str,
        vol.Optional(CONF_SCAN_INTERVAL): int,
        vol.Optional(CONF_NETWORK_RETRIES): cv.positive_int,
        vol.Optional(CONF_NETWORK_TIMEOUT): cv.positive_int,
    }
)

_LOGGER = logging.getLogger(__name__)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                {
                    CONF_HOST: self.config_entry.data[CONF_HOST],
                    CONF_PROTOCOL: self.config_entry.data.get(CONF_PROTOCOL, "UDP"),
                    CONF_KEEP_ALIVE: self.config_entry.options.get(
                        CONF_KEEP_ALIVE,
                        self.config_entry.data.get(CONF_PROTOCOL) != "TCP",
                    ),
                    CONF_MODEL_FAMILY: self.config_entry.data[CONF_MODEL_FAMILY],
                    CONF_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_NETWORK_RETRIES: self.config_entry.options.get(
                        CONF_NETWORK_RETRIES, DEFAULT_NETWORK_RETRIES
                    ),
                    CONF_NETWORK_TIMEOUT: self.config_entry.options.get(
                        CONF_NETWORK_TIMEOUT, DEFAULT_NETWORK_TIMEOUT
                    ),
                },
            ),
        )


class GoodweFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Goodwe config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            protocol = user_input[CONF_PROTOCOL]
            model_family = user_input[CONF_MODEL_FAMILY]
            port = 502 if protocol == "TCP" else 8899

            try:
                inverter = await connect(
                    host=host, port=port, family=model_family, retries=10
                )
            except InverterError:
                errors[CONF_HOST] = "connection_error"
            else:
                await self.async_set_unique_id(inverter.serial_number)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={
                        CONF_HOST: host,
                        CONF_PROTOCOL: protocol,
                        CONF_MODEL_FAMILY: type(inverter).__name__,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )
