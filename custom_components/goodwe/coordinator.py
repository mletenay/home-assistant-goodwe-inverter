"""Update coordinator for Goodwe."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from goodwe import Inverter, InverterError, RequestFailedException
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import (
    BaseCoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_WAKEUP_INTERVAL
from .wakeup import async_send_wakeup_packet

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
        wakeup_host: str | None = None,
        wakeup_interval: int = DEFAULT_WAKEUP_INTERVAL,
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
        self._wakeup_host = wakeup_host
        try:
            wakeup_interval_minutes = max(1, int(wakeup_interval))
        except (TypeError, ValueError):
            wakeup_interval_minutes = DEFAULT_WAKEUP_INTERVAL
        self._wakeup_interval = timedelta(minutes=wakeup_interval_minutes)
        self._last_wakeup_attempt: datetime | None = None
        self._cancel_wakeup_interval: CALLBACK_TYPE | None = None

        if self._wakeup_host:
            self._cancel_wakeup_interval = async_track_time_interval(
                hass,
                self._async_wakeup_interval,
                self._wakeup_interval,
                name=f"goodwe_wakeup_{entry.entry_id}",
            )
            entry.async_on_unload(self._cancel_wakeup_interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the inverter."""
        await self._update_polled_entities()

        try:
            self._last_data = self.data or {}
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
            await self._async_send_wakeup_packet("communication failure", throttle=True)
            raise UpdateFailed(ex) from ex
        except InverterError as ex:
            raise UpdateFailed(ex) from ex

    async def _async_wakeup_interval(self, _: datetime) -> None:
        """Send the scheduled wake-up packet."""
        await self._async_send_wakeup_packet("scheduled interval")

    async def _async_send_wakeup_packet(
        self, reason: str, throttle: bool = False
    ) -> None:
        """Send a wake-up packet if the opt-in wake-up option is enabled."""
        if not self._wakeup_host:
            return

        now = datetime.now()
        if (
            throttle
            and self._last_wakeup_attempt
            and now - self._last_wakeup_attempt < self._wakeup_interval
        ):
            return

        self._last_wakeup_attempt = now
        _LOGGER.debug("Sending GoodWe wake-up packet after %s", reason)
        await async_send_wakeup_packet(self._wakeup_host, _LOGGER)

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
        return val or self._last_data.get(sensor)

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
