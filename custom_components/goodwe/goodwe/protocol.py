import asyncio
import logging
from typing import Tuple, Optional, Callable

from .exceptions import MaxRetriesException, RequestFailedException
from .utils import create_crc16_table

logger = logging.getLogger(__name__)


class UdpInverterProtocol(asyncio.DatagramProtocol):
    def __init__(
            self,
            request: bytes,
            validator: Callable[[bytes], bool],
            on_response_received: asyncio.futures.Future,
            timeout: int = 2,
            retries: int = 3
    ):
        super().__init__()
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator
        self.on_response_received: asyncio.futures.Future = on_response_received
        self.transport: asyncio.transports.DatagramTransport
        self._retry_timeout: int = timeout
        self._max_retries: int = retries
        self._retries: int = 0

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """On connection made"""
        logger.debug(f'Connection made to address {transport.get_extra_info("peername")}')
        self.transport = transport
        self._send_request()

    def _send_request(self) -> None:
        """Send message via transport"""
        logger.debug(f'Sent: {self.request.hex()}')
        self.transport.sendto(self.request)
        asyncio.get_event_loop().call_later(self._retry_timeout, self.retry_mechanism)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """On connection lost"""
        if exc is not None:
            logger.debug(f'Socket closed with error: {exc}')
        # Cancel Future on connection lost
        if not self.on_response_received.done():
            self.on_response_received.cancel()

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """On datagram received"""
        logger.debug(f'Received: {data.hex()}')
        if self.validator(data):
            self.on_response_received.set_result(data)
        else:
            logger.debug(f'Invalid response: {data.hex()}')
            self._retries += 1
            self._send_request()

    def error_received(self, exc: Exception) -> None:
        """On error received"""
        logger.debug(f'Received error: {exc}')
        self.on_response_received.set_exception(exc)

    def retry_mechanism(self):
        """Retry mechanism to prevent hanging transport"""
        # If future is done we can close the transport
        if self.on_response_received.done():
            self.transport.close()
        elif self._retries < self._max_retries:
            self._retries += 1
            logger.debug(f'Retry #{self._retries + 1} of {self._max_retries}')
            self._send_request()
        else:
            logger.debug(f'Max number of retries ({self._max_retries}) reached, closing socket')
            self.on_response_received.set_exception(MaxRetriesException)
            self.transport.close()


class ProtocolCommand:
    """Definition of inverter protocol command"""

    def __init__(self, request: bytes, validator: Callable[[bytes], bool]):
        self.request: bytes = request
        self.validator: Callable[[bytes], bool] = validator

    async def execute(self, host: str, port: int, timeout: int = 2, retries: int = 3) -> bytes:
        """
        Execute the udp protocol command on the specified address/port.
        Since the UDP communication is by definition unreliable, when no (valid) response is received by specified
        timeout, the command will be re-tried up to retries times.

        Return raw response data
        """
        loop = asyncio.get_running_loop()
        on_response_received = loop.create_future()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: UdpInverterProtocol(
                self.request, self.validator, on_response_received, timeout, retries
            ),
            remote_addr=(host, port),
        )
        try:
            await on_response_received
            result = on_response_received.result()
            if result is not None:
                return result
            else:
                raise RequestFailedException(
                    "No response received to '" + self.request.hex() + "' request"
                )
        except asyncio.CancelledError:
            raise RequestFailedException(
                "No valid response received to '" + self.request.hex() + "' request"
            ) from None
        finally:
            transport.close()


class Aa55ProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol based on 0xAA,0x55 kinds of commands.
    Each comand starts with header of 0xAA, 0x55, 0xC0, 0x7F followed by payload data.
    It is suffixed with 2 bytes of plain checksum of header+payload.
    """

    def __init__(self, payload: str, response_type: str):
        super().__init__(
            bytes.fromhex(
                "AA55C07F"
                + payload
                + self._checksum(bytes.fromhex("AA55C07F" + payload)).hex()
            ),
            lambda x: self._validate_response(x, response_type),
        )

    @staticmethod
    def _checksum(data: bytes) -> bytes:
        checksum = 0
        for each in data:
            checksum += each
        return checksum.to_bytes(2, byteorder="big", signed=False)

    @staticmethod
    def _validate_response(data: bytes, response_type: str) -> bool:
        """
        Validate the response.
        data[0:3] is header
        data[4:5] is response type
        data[6] is response payload length
        data[-2:] is checksum (plain sum of response data incl. header)
        """
        if (
                len(data) <= 8
                or len(data) != data[6] + 9
                or (response_type and int(response_type, 16) != _read_bytes2(data[4:6], 0))
        ):
            return False
        else:
            checksum = 0
            for each in data[:-2]:
                checksum += each
            return checksum == _read_bytes2(data[-2:], 0)


class ModbusProtocolCommand(ProtocolCommand):
    """
    Inverter communication protocol, suffixes each payload with 2 bytes of Modbus-CRC16 checksum of the payload.
    """

    _CRC_16_TABLE = create_crc16_table()

    def __init__(self, payload: str, response_len: int = 0):
        super().__init__(
            bytes.fromhex(
                payload + self._checksum(bytes.fromhex(payload))
            ),
            lambda x: self._validate_response(x, response_len),
        )

    @classmethod
    def _checksum(cls, data: bytes) -> str:
        crc = 0xFFFF
        for ch in data:
            crc = (crc >> 8) ^ cls._CRC_16_TABLE[(crc ^ ch) & 0xFF]
        res = "{:04x}".format(crc)
        return res[2:] + res[:2]

    @classmethod
    def _validate_response(cls, data: bytes, response_len: int) -> bool:
        """
        Validate the response.
        data[0:1] is header
        data[2:3] is response type
        data[4] is response payload length ??
        data[-2:] is crc-16 checksum
        """
        if len(data) <= 4 or (response_len != 0 and response_len != len(data)):
            return False
        return cls._checksum(data[2:-2]) == data[-2:].hex()


def _read_bytes2(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset: offset + 2], byteorder="big", signed=True)
