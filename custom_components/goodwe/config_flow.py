"""Config flow to configure Goodwe inverters using their local API."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers import config_validation as cv
from homeassistant.core import callback

from .goodwe.goodwe import connect, InverterError

from .const import CONF_COMM_ADDRESS, CONF_MODEL_FAMILY, DEFAULT_NAME, DOMAIN, DEFAULT_SCAN_INTERVAL

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_COMM_ADDRESS): cv.positive_int,
    }
)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Init object."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        settings_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=settings_schema)


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

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            comm_address = user_input.get(CONF_COMM_ADDRESS)

            try:
                inverter = await connect(
                    host = host,
                    comm_addr = comm_address,
                )
            except InverterError as err:
                errors["base"] = "connection_error"

            if not errors:
                await self.async_set_unique_id(inverter.serial_number)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={
                        CONF_HOST: host
                        CONF_COMM_ADDRESS: inverter.comm_addr
                        CONF_MODEL_FAMILY: type(inverter).__name__
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

