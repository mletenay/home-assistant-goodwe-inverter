"""Update coordinator for Goodwe."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from goodwe import Inverter, InverterError, RequestFailedException, ProtocolCommand, \
    UdpInverterProtocol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, CALLBACK_TYPE
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import (
    BaseCoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type GoodweConfigEntry = ConfigEntry[GoodweRuntimeData]


@dataclass
class GoodweRuntimeData:
    """Data class for runtime data."""

    inverter: Inverter
    coordinator: GoodweUpdateCoordinator
    device_info: DeviceInfo


class GoodweUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Gather data for the energy device."""

    config_entry: GoodweConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoodweConfigEntry,
        inverter: Inverter,
    ) -> None:
        """Initialize update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.inverter: Inverter = inverter
        self._last_data: dict[str, Any] = {}
        self._polled_entities: dict[BaseCoordinatorEntity, datetime] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter."""
        await self._update_polled_entities()

        try:
            self._last_data = self.data if self.data else {}
            return await self.inverter.read_runtime_data()
        except RequestFailedException as ex:
            # UDP communication with inverter is by definition unreliable.
            # It is rather normal in many environments to fail to receive
            # proper response in usual time, so we intentionally ignore isolated
            # failures and report problem with availability only after
            # consecutive streak of 3 of failed requests.
            if ex.consecutive_failures_count < 3:
                _LOGGER.debug(
                    "No response received (streak of %d)", ex.consecutive_failures_count
                )
                # return last known data
                return self._last_data
            # Inverter does not respond anymore (e.g. it went to sleep mode)
            _LOGGER.debug(
                "Inverter not responding (streak of %d)", ex.consecutive_failures_count
            )
            raise UpdateFailed(ex) from ex
        except InverterError as ex:
            raise UpdateFailed(ex) from ex

    async def _update_polled_entities(self) -> None:
        for entity, interval in list(self._polled_entities.items()):
            if interval:
                try:
                    await entity.async_update()
                except InverterError:
                    _LOGGER.debug("Failed to update entity %s", entity.name)

    def sensor_value(self, sensor: str) -> Any:
        """Answer current (or last known) value of the sensor."""
        val = self.data.get(sensor)
        return val if val is not None else self._last_data.get(sensor)

    def total_sensor_value(self, sensor: str) -> Any:
        """Answer current value of the 'total' (never 0) sensor."""
        val = self.data.get(sensor)
        return val if val else self._last_data.get(sensor)

    def reset_sensor(self, sensor: str) -> None:
        """Reset sensor value to 0.

        Intended for "daily" cumulative sensors (e.g. PV energy produced today),
        which should be explicitly reset to 0 at midnight if inverter is suspended.
        """
        self._last_data[sensor] = 0
        self.data[sensor] = 0

    def entity_state_polling(
        self, entity: BaseCoordinatorEntity, interval: int
    ) -> None:
        """Enable/disable polling of entity state."""
        if interval:
            self._polled_entities[entity] = interval
        else:
            self._polled_entities.pop(entity, None)


class GoodweUpdateCoordinatorWithWakeUp(GoodweUpdateCoordinator):
    _host: str
    _cancel_wakeup_interval: CALLBACK_TYPE | None

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoodweConfigEntry,
        inverter: Inverter,
        host: str,
    ):
        super().__init__(hass=hass, entry=entry, inverter=inverter)
        self._host = host
        self.logger.debug(f"setting up start event, ha is running: {hass.is_running}")
        hass.create_task(target=self._start_wakeup_interval(), name="start wakeup interval")
        self.logger.debug(f"task scheduled")

    async def _start_wakeup_interval(self):
        self.logger.debug("setting up wakeup packet interval")

        async def on_wakeup_interval(_):
            self.logger.debug("received wakeup interval event, sending wakeup packet")
            await self._send_wakeup_packet()
            self.logger.debug("wakeup packet sent from wakeup interval event")

        self._cancel_wakeup_interval = async_track_time_interval(
            hass=self.hass,
            action=on_wakeup_interval,
            interval=timedelta(minutes=1),
            name="goodwe_inverter_send_wakeup_packet"
        )

        # send a wakeup packet on start as well just to be safe
        self.logger.debug("sending initial wakeup packet")
        await self._send_wakeup_packet()
        self.logger.debug("initial wakeup packet sent")

    async def async_shutdown(self):
        self.logger.debug("shutdown called")
        if self._cancel_wakeup_interval:
            self.logger.debug("cancelling wakeup interval")
            self._cancel_wakeup_interval()
            self._cancel_wakeup_interval = None

        return super().async_shutdown()

    async def _send_wakeup_packet(self) -> None:
        return await send_wakeup_packet(logger=self.logger, host=self._host)


async def send_wakeup_packet(logger: logging.Logger, host: str) -> None:
    logger.debug("Sending wakeup packet to inverter on port 48899")
    command = ProtocolCommand("WIFIKIT-214028-READ".encode("utf-8"), lambda r: True)
    try:
        result = await command.execute(UdpInverterProtocol(host=host, port=48899, comm_addr=1, timeout=1))
        if result is not None:
            raw_data = result.response_data()
            logger.debug(f"Received response from wakeup packet: {repr(raw_data)}")
        else:
            logger.debug(f"No response received from wakeup packet")
    except asyncio.CancelledError:
        logger.debug(f"No valid response received to wakeup packet")
