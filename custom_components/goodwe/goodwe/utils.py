import io
from datetime import datetime
from typing import Optional

from .const import *


def read_byte(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve single byte (signed int) value from buffer at given position"""
    buffer.seek(offset)
    return int.from_bytes(buffer.read(1), byteorder="big", signed=True)


def read_bytes2(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve 2 byte (signed int) value from buffer at given position"""
    buffer.seek(offset)
    return int.from_bytes(buffer.read(2), byteorder="big", signed=True)


def read_bytes4(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve 4 byte (signed int) value from buffer at given position"""
    buffer.seek(offset)
    return int.from_bytes(buffer.read(4), byteorder="big", signed=True)


def read_voltage(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve voltage [V] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def read_current(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve current [A] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    if value > 32768:
        value = value - 65535
    return float(value) / 10


def read_power(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve power [W] value (4 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(4), byteorder="big", signed=True)
    if value > 32768:
        value = value - 65535
    return value


def read_power2(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve power [W] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    if value > 32768:
        value = value - 65535
    return value


def read_power_k(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve power [kW] value (4 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(4), byteorder="big", signed=True)
    return float(value) / 10


def read_power_k2(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve power [kW] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def read_freq(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve frequency [Hz] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 100


def read_temp(buffer: io.BytesIO, offset: int) -> float:
    """Retrieve temperature [C] value (2 bytes) from buffer at given position"""
    buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def read_datetime(buffer: io.BytesIO, offset: int) -> datetime:
    """Retrieve datetime value (6 bytes) from buffer at given position"""
    buffer.seek(offset)
    year = 2000 + int.from_bytes(buffer.read(1), byteorder='big')
    month = int.from_bytes(buffer.read(1), byteorder='big')
    day = int.from_bytes(buffer.read(1), byteorder='big')
    hour = int.from_bytes(buffer.read(1), byteorder='big')
    minute = int.from_bytes(buffer.read(1), byteorder='big')
    second = int.from_bytes(buffer.read(1), byteorder='big')
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


def read_grid_mode(buffer: io.BytesIO, offset: int) -> int:
    """Retrieve 'grid mode' sign value from buffer at given position"""
    value = read_power(buffer, offset)
    if value < -90:
        return 2
    elif value >= 90:
        return 1
    else:
        return 0


def read_battery_mode(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'battery mode label' value from buffer at given position"""
    return BATTERY_MODES_ET.get(read_bytes2(buffer, offset))


def read_safety_country(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'safe country label' value from buffer at given position"""
    return SAFETY_COUNTRIES_ET.get(read_bytes2(buffer, offset))


def read_work_mode_et(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'work mode (ET) label' value from buffer at given position"""
    return WORK_MODES_ET.get(read_bytes2(buffer, offset))


def read_work_mode_dt(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'work mode (DT) label' value from buffer at given position"""
    return WORK_MODES.get(read_bytes2(buffer, offset))


def read_work_mode1(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'work mode (ES) label' value from buffer at given position"""
    return WORK_MODES_ES.get(read_byte(buffer, offset))


def read_pv_mode1(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'PV mode label' value from buffer at given position"""
    return PV_MODES.get(read_byte(buffer, offset))


def read_load_mode1(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'load mode label' value from buffer at given position"""
    return LOAD_MODES.get(read_byte(buffer, offset))


def read_energy_mode1(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'energy mode label' value from buffer at given position"""
    return ENERGY_MODES.get(read_byte(buffer, offset))


def read_battery_mode1(buffer: io.BytesIO, offset: int) -> Optional[str]:
    """Retrieve 'battery mode label' value from buffer at given position"""
    return BATTERY_MODES_ET.get(read_byte(buffer, offset))
