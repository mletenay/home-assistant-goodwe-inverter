"""Wake-up support for GoodWe WiFi/LAN adapters."""

from __future__ import annotations

import asyncio
import logging

from goodwe import InverterError, ProtocolCommand, UdpInverterProtocol

_WAKEUP_PORT = 48899
_WAKEUP_PAYLOAD = b"WIFIKIT-214028-READ"


async def async_send_wakeup_packet(host: str, logger: logging.Logger) -> bool:
    """Send a WiFi/LAN adapter discovery packet used to wake some adapters."""
    command = ProtocolCommand(_WAKEUP_PAYLOAD, lambda response: True)
    try:
        result = await command.execute(
            UdpInverterProtocol(
                host=host,
                port=_WAKEUP_PORT,
                comm_addr=1,
                timeout=1,
                retries=0,
            )
        )
    except asyncio.CancelledError:
        raise
    except (
        ConnectionRefusedError,
        InverterError,
        OSError,
    ) as err:
        logger.debug("No response received from GoodWe wake-up packet: %s", err)
        return False

    if result is None:
        logger.debug("No response received from GoodWe wake-up packet")
        return False

    logger.debug(
        "Received response from GoodWe wake-up packet: %r", result.response_data()
    )
    return True
