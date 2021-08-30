import logging

from typing import Union

logger = logging.getLogger(__name__)

# default inverter modbus address
_INVERTER_ADDRESS = 0xf7

MODBUS_READ_CMD: int = 0x3
MODBUS_WRITE_CMD: int = 0x6


def _create_crc16_table() -> tuple:
    """Construct (modbus) CRC-16 table"""
    table = []
    for i in range(256):
        buffer = i << 1
        crc = 0
        for _ in range(8, 0, -1):
            buffer >>= 1
            if (buffer ^ crc) & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
        table.append(crc)
    return tuple(table)


_CRC_16_TABLE = _create_crc16_table()


def _modbus_checksum(data: Union[bytearray, bytes]) -> int:
    """
    Calculate modbus crc-16 checksum
    """
    crc = 0xFFFF
    for ch in data:
        crc = (crc >> 8) ^ _CRC_16_TABLE[(crc ^ ch) & 0xFF]
    return crc


def create_modbus_request(cmd: int, offset: int, count: int) -> bytes:
    """
    Create modbus request.
    data[0] is inverter address
    data[1] is modbus command
    data[2:3] is command offset parameter
    data[4:5] is command count parameter
    data[6:7] is crc-16 checksum
    """
    data: bytearray = bytearray(6)
    data[0] = _INVERTER_ADDRESS
    data[1] = cmd
    data[2] = (offset >> 8) & 0xFF
    data[3] = offset & 0xFF
    data[4] = (count >> 8) & 0xFF
    data[5] = count & 0xFF
    checksum = _modbus_checksum(data)
    data.append(checksum & 0xFF)
    data.append((checksum >> 8) & 0xFF)
    return bytes(data)


def append_modbus_checksum(payload: str) -> bytes:
    """
    Create modbus request from prepared string payload
    """
    data = bytearray.fromhex(payload)
    checksum = _modbus_checksum(data)
    data.append(checksum & 0xFF)
    data.append((checksum >> 8) & 0xFF)
    return bytes(data)


def validate_modbus_response(data: bytes) -> bool:
    """
    Validate the modbus response.
    data[0:1] is header
    data[2:3] is response type
    data[4] is response payload length
    data[-2:] is crc-16 checksum
    """
    if len(data) <= 4 or (data[4] > len(data) - 7):
        logger.debug(f'Response has unexpected length: {len(data)}, expected {data[4] + 7}.')
        return False
    checksum_offset = data[4] + 5
    if _modbus_checksum(data[2:checksum_offset]) != ((data[checksum_offset + 1] << 8) + data[checksum_offset]):
        logger.debug(f'Response CRC-16 checksum does not match.')
        return False
    return True
