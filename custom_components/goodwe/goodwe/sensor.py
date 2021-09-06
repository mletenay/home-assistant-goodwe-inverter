import io
import struct
from datetime import datetime
from typing import Any, Callable, Optional

from .const import *
from .inverter import Sensor, SensorKind


class Voltage(Sensor):
    """Sensor representing voltage [V] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "V", kind)

    def read_value(self, data: io.BytesIO):
        return read_voltage(data)

    def encode_value(self, value: Any) -> bytes:
        return encode_voltage(value)


class Current(Sensor):
    """Sensor representing current [A] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "A", kind)

    def read_value(self, data: io.BytesIO):
        return read_current(data)

    def encode_value(self, value: Any) -> bytes:
        return encode_current(value)


class Frequency(Sensor):
    """Sensor representing frequency [Hz] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "Hz", kind)

    def read_value(self, data: io.BytesIO):
        return read_freq(data)


class Power(Sensor):
    """Sensor representing power [W] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "W", kind)

    def read_value(self, data: io.BytesIO):
        return read_power2(data)


class Power4(Sensor):
    """Sensor representing power [W] value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "W", kind)

    def read_value(self, data: io.BytesIO):
        return read_power(data)


class PowerK(Sensor):
    """Sensor representing power [kW] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "kW", kind)

    def read_value(self, data: io.BytesIO):
        return read_power_k2(data)


class PowerK4(Sensor):
    """Sensor representing power [kW] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "kW", kind)

    def read_value(self, data: io.BytesIO):
        return read_power_k(data)


class Energy(Sensor):
    """Sensor representing power [W] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "kWh", kind)

    def read_value(self, data: io.BytesIO):
        return read_power_k2(data)


class Energy4(Sensor):
    """Sensor representing power [W] value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind]):
        super().__init__(id_, offset, name, "kWh", kind)

    def read_value(self, data: io.BytesIO):
        return read_power_k(data)


class Temp(Sensor):
    """Sensor representing temperature [C] value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, "C", kind)

    def read_value(self, data: io.BytesIO):
        return read_temp(data)


class Byte(Sensor):
    """Sensor representing signed int value encoded in 1 byte"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)

    def read_value(self, data: io.BytesIO):
        return read_byte(data)

    def encode_value(self, value: Any) -> bytes:
        return int.to_bytes(int(value), length=1, byteorder="big", signed=True)


class Integer(Sensor):
    """Sensor representing signed int value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)

    def read_value(self, data: io.BytesIO):
        return read_bytes2(data)

    def encode_value(self, value: Any) -> bytes:
        return int.to_bytes(int(value), length=2, byteorder="big", signed=True)


class Long(Sensor):
    """Sensor representing signed int value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)

    def read_value(self, data: io.BytesIO):
        return read_bytes4(data)

    def encode_value(self, value: Any) -> bytes:
        return int.to_bytes(int(value), length=4, byteorder="big", signed=True)


class Decimal(Sensor):
    """Sensor representing signed decimal value encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, scale: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)
        self.scale = scale

    def read_value(self, data: io.BytesIO):
        return read_decimal2(data, self.scale)

    def encode_value(self, value: Any) -> bytes:
        return int.to_bytes(int(value * self.scale), length=2, byteorder="big", signed=True)


class Float(Sensor):
    """Sensor representing signed int value encoded in 4 bytes"""

    def __init__(self, id_: str, offset: int, scale: int, name: str, unit: str = "", kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)
        self.scale = scale

    def read_value(self, data: io.BytesIO):
        return round(read_float4(data) / self.scale, 3)


class Timestamp(Sensor):
    """Sensor representing datetime value encoded in 6 bytes"""

    def __init__(self, id_: str, offset: int, name: str, kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, "", kind)

    def read_value(self, data: io.BytesIO):
        return read_datetime(data)


class Enum(Sensor):
    """Sensor representing label from enumeration encoded in 1 bytes"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, unit: str = "",
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)
        self.labels: Dict = labels

    def read_value(self, data: io.BytesIO):
        return self.labels.get(read_byte(data))


class Enum2(Sensor):
    """Sensor representing label from enumeration encoded in 2 bytes"""

    def __init__(self, id_: str, offset: int, labels: Dict, name: str, unit: str = "",
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)
        self.labels: Dict = labels

    def read_value(self, data: io.BytesIO):
        return self.labels.get(read_bytes2(data))


class Calculated(Sensor):
    """Sensor representing calculated value"""

    def __init__(self, id_: str, offset: int, getter: Callable[[io.BytesIO, int], Any], name: str, unit: str,
                 kind: Optional[SensorKind] = None):
        super().__init__(id_, offset, name, unit, kind)
        self._getter: Callable[[io.BytesIO, int], Any] = getter

    def read_value(self, data: io.BytesIO) -> Any:
        raise NotImplementedError()

    def read(self, data: io.BytesIO):
        data.seek(self.offset)
        return self._getter(data, self.offset)


def read_byte(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve single byte (signed int) value from buffer"""
    if offset:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(1), byteorder="big", signed=True)


def read_bytes2(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve 2 byte (signed int) value from buffer"""
    if offset:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(2), byteorder="big", signed=True)


def read_bytes4(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve 4 byte (signed int) value from buffer"""
    if offset:
        buffer.seek(offset)
    return int.from_bytes(buffer.read(4), byteorder="big", signed=True)


def read_decimal2(buffer: io.BytesIO, scale: int, offset: int = None) -> float:
    """Retrieve 2 byte (signed float) value from buffer"""
    if offset:
        buffer.seek(offset)
    return float(int.from_bytes(buffer.read(2), byteorder="big", signed=True)) / scale


def read_float4(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve 4 byte (signed float) value from buffer"""
    if offset:
        buffer.seek(offset)
    data = buffer.read(4)
    if len(data) == 4:
        return struct.unpack('>f', data)[0]
    else:
        return float(0)


def read_voltage(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve voltage [V] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def encode_voltage(value: Any) -> bytes:
    """Encode voltage value to raw (2 bytes) payload"""
    return int.to_bytes(int(value * 10), length=2, byteorder="big", signed=True)


def read_current(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve current [A] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def encode_current(value: Any) -> bytes:
    """Encode current value to raw (2 bytes) payload"""
    return int.to_bytes(int(value * 10), length=2, byteorder="big", signed=True)


def read_power(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve power [W] value (4 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(4), byteorder="big", signed=True)
    if value > 32768:
        value = value - 65535
    return value


def read_power2(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve power [W] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return value


def read_power_k(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve power [kW] value (4 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(4), byteorder="big", signed=True)
    return float(value) / 10


def read_power_k2(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve power [kW] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def read_freq(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve frequency [Hz] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 100


def read_temp(buffer: io.BytesIO, offset: int = None) -> float:
    """Retrieve temperature [C] value (2 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    value = int.from_bytes(buffer.read(2), byteorder="big", signed=True)
    return float(value) / 10


def read_datetime(buffer: io.BytesIO, offset: int = None) -> datetime:
    """Retrieve datetime value (6 bytes) from buffer"""
    if offset:
        buffer.seek(offset)
    year = 2000 + int.from_bytes(buffer.read(1), byteorder='big')
    month = int.from_bytes(buffer.read(1), byteorder='big')
    day = int.from_bytes(buffer.read(1), byteorder='big')
    hour = int.from_bytes(buffer.read(1), byteorder='big')
    minute = int.from_bytes(buffer.read(1), byteorder='big')
    second = int.from_bytes(buffer.read(1), byteorder='big')
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)


def read_grid_mode(buffer: io.BytesIO, offset: int = None) -> int:
    """Retrieve 'grid mode' sign value from buffer"""
    value = read_power(buffer, offset)
    if value < -90:
        return 2
    elif value >= 90:
        return 1
    else:
        return 0


def read_unsigned_int(data: bytes, offset: int) -> int:
    """Retrieve 2 byte (unsigned int) value from bytes at specified offset"""
    return int.from_bytes(data[offset:offset + 2], byteorder="big", signed=False)


def decode_bitmap(value: int, bitmap: Dict[int, str]) -> str:
    bits = value
    result = []
    for i in range(32):
        if bits & 0x1 == 1:
            result.append(bitmap.get(i))
        bits = bits >> 1
    return ", ".join(result)
