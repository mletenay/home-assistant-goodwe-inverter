"""The GoodWe inverter data retrieval module"""
import asyncio
import logging
from collections import namedtuple

_LOGGER = logging.getLogger(__name__)

_ICON_PV = "mdi:solar-power"
_ICON_AC = "mdi:power-plug-outline"
_ICON_AC_BACK = "mdi:power-plug-off-outline"
_ICON_BATT = "mdi:battery-high"

_WORK_MODES_ET = {
    0: "Wait Mode",
    1: "Normal(On-Grid)",
    2: "Normal(Off-Grid)",
    3: "Fault Mode",
    4: "Flash Mode",
    5: "Check Mode",
}

_BATTERY_MODES_ET = {
    0: "No battery or battery disconnected",
    1: "Spare",
    2: "Discharge",
    3: "Charge",
    4: "To be charged",
    5: "To be discharged",
}

_PV_MODES = {
    0: "Disconnect the inverter and PV panels",
    1: "No power output PV",
    2: "Working,PV has a power output",
}

_LOAD_MODES = {
    0: "The inverter is connected to a load",
    1: "Inverter and the load is disconnected",
}

_WORK_MODES = {
    0: "Wait for the conditions to generate electricity",
    1: "The inverter is generating",
    2: "System abnormalities, while stopping power",
    3: "System is severely abnormal, 20 seconds after the restart",
}

_ENERGY_MODES = {
    0: "Check Mode",
    1: "Wait Mode",
    2: "Normal(On-Grid)",
    4: "Normal(Off-Grid)",
    8: "Flash Mode",
    16: "Fault Mode",
    32: "Battery Standby",
    64: "Battery Charging",
    128: "Battery Discharging",
}

_GRID_MODES = {
    0: "Inverter neither send power to grid,nor get power from grid",
    1: "Inverter sends power to grid",
    2: "Inverter gets power from grid",   
}

_SAFETY_COUNTRIES_ET = {
    0: "Italy",
    1: "Czech",
    2: "Germany",
    3: "Spain",
    4: "Greece",
    5: "Denmark",
    6: "Belguim",
    7: "Romania",
    8: "G98",
    9: "Australia",
    10: "France",
    11: "China",
    13: "Poland",
    14: "South Africa",
    15: "AustraliaL",
    16: "Brazil",
    17: "Thailand MEA",
    18: "Thailand PEA",
    19: "Mauritius",
    20: "Holland",
    21: "Northern Ireland",
    22: "China Higher",
    23: "French 50Hz",
    24: "French 60Hz",
    25: "Australia Ergon",
    26: "Australia Energex",
    27: "Holland 16/20A",
    28: "Korea",
    29: "China Station",
    30: "Austria",
    31: "India",
    32: "50Hz Grid Default",
    33: "Warehouse",
    34: "Philippines",
    35: "Ireland",
    36: "Taiwan",
    37: "Bulgaria",
    38: "Barbados",
    39: "China Highest",
    40: "G99",
    41: "Sweden",
    42: "Chile",
    43: "Brazil LV",
    44: "NewZealand",
    45: "IEEE1547 208VAC",
    46: "IEEE1547 220VAC",
    47: "IEEE1547 240VAC",
    48: "60Hz LV Default",
    49: "50Hz LV Default",
    50: "AU_WAPN",
    51: "AU_MicroGrid",
    52: "JP_50Hz",
    53: "JP_60Hz",
    54: "India Higher",
    55: "DEWA LV",
    56: "DEWA MV",
    57: "Slovakia",
    58: "GreenGrid",
    59: "Hungary",
    60: "Sri Lanka",
    61: "Spain Islands",
    62: "Ergon30K",
    63: "Energex30K",
    64: "IEEE1547 230/400V",
    65: "IEC61727 60Hz",
    66: "Switzerland",
    67: "CEI-016",
    68: "AU_Horizon",
    69: "Cyprus",
    70: "AU_SAPN",
    71: "AU_Ausgrid",
    72: "AU_Essential",
    73: "AU_Pwcore&CitiPW",
    74: "Hong Kong",
    75: "Poland MV",
    76: "Holland MV",
    77: "Sweden MV",
    78: "VDE4110",
    96: "cUSA_208VacDefault",
    97: "cUSA_240VacDefault",
    98: "cUSA_208VacCA_SCE",
    99: "cUSA_240VacCA_SCE",
    100: "cUSA_208VacCA_SDGE",
    101: "cUSA_240VacCA_SDGE",
    102: "cUSA_208VacCA_PGE",
    103: "cUSA_240VacCA_PGE",
    104: "cUSA_208VacHECO_14HO",
    105: "cUSA_240VacHECO_14HO0x69",
    106: "cUSA_208VacHECO_14HM",
    107: "cUSA_240VacHECO_14HM",
}


def _read_voltage(data, offset):
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 10


def _read_current(data, offset):
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_power(data, offset):
    value = (
        (data[offset] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )
    if value > 32768:
        value = value - 65536
    return value


def _read_power2(data, offset):
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return value


def _read_power_k(data, offset):
    value = (
        (data[offset] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_power_k2(data, offset):
    value = (data[offset] << 8) | data[offset + 1]
    if value > 32768:
        value = value - 65536
    return float(value) / 10


def _read_freq(data, offset):
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 100


def _read_temp(data, offset):
    # Shift to real offset, 1000 is the marker
    if offset > 1000:
        offset -= 1000
    value = (data[offset] << 8) | data[offset + 1]
    return float(value) / 10


def _read_byte(data, offset):
    # Shift to real offset, 1000 is the marker
    if offset >= 1000:
        offset -= 1000
    return data[offset]


def _read_bytes2(data, offset):
    # Shift to real offset, 1000 is the marker
    if offset >= 1000:
        offset -= 1000
    return (data[offset] << 8) | data[offset + 1]


def _read_bytes4(data, offset):
    return (
        (data[offset + 0] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )


def _read_grid_mode(data, offset):
    value = _read_bytes4(data, offset)
    if value > 32768:
        value -= 65535
    if value < -90:
        return 2
    elif value >= 90:
        return 1
    else:
        return 0


def _read_battery_mode(data, offset):
    return _BATTERY_MODES_ET.get(_read_bytes2(data, offset))


def _read_safety_country(data, offset):
    return _SAFETY_COUNTRIES_ET.get(_read_bytes2(data, offset))


def _read_work_mode(data, offset):
    return _WORK_MODES_ET.get(_read_bytes2(data, offset))


def _read_pv_mode1(data, offset):
    return _PV_MODES.get(_read_byte(data, offset))


def _read_work_mode1(data, offset):
    return _WORK_MODES.get(_read_byte(data, offset))


def _read_load_mode1(data, offset):
    return _LOAD_MODES.get(_read_byte(data, offset))


def _read_energy_mode1(data, offset):
    return _ENERGY_MODES.get(_read_byte(data, offset))


def _read_grid_mode1(data, offset):
    return _GRID_MODES.get(_read_byte(data, offset))


def _read_battery_mode1(data, offset):
    return _BATTERY_MODES_ET.get(_read_byte(data, offset))


class _UdpInverterProtocol(asyncio.DatagramProtocol):
    def __init__(self, request, response_lenghts, on_response_received, timeout=2):
        self.request = request
        self.response_lenghts = response_lenghts
        self.on_response_received = on_response_received
        self.transport = None
        self.timeout = timeout
        self.retry_nr = 1

    def connection_made(self, transport):
        self.transport = transport
        _LOGGER.debug("Send: '%s'", self.request.hex())
        self.transport.sendto(self.request)
        asyncio.get_event_loop().call_later(self.timeout, self._timeout_heartbeat)

    def connection_lost(self, exc):
        if exc is not None:
            _LOGGER.debug("Socket closed with error: '%s'", exc)    
        if not self.on_response_received.done():
            self.on_response_received.cancel()

    def datagram_received(self, data, addr):
        _LOGGER.debug("Received: '%s'", data.hex())
        if len(data) in self.response_lenghts:
            self.on_response_received.set_result(data)
            self.transport.close()
        else:
            _LOGGER.debug(
                "Unexpected response length: expected %s, received: %d",
                self.response_lenghts,
                len(data),
            )
            self.retry_nr += 1
            self.connection_made(self.transport)

    def error_received(self, exc):
        _LOGGER.debug("Received error: '%s'", exc)

    def _timeout_heartbeat(self):
        if self.on_response_received.done():
            self.transport.close()
        elif self.retry_nr < 4:
            _LOGGER.debug("Timeout #%d", self.retry_nr)
            self.retry_nr += 1
            self.connection_made(self.transport)
        else:
            _LOGGER.debug("Timeout #%d, closing socket", self.retry_nr)
            self.transport.close()


async def _read_from_socket(command_spec, inverter_address):
    loop = asyncio.get_running_loop()
    on_response_received = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _UdpInverterProtocol(
            command_spec[0], command_spec[1], on_response_received
        ),
        remote_addr=inverter_address,
    )
    try:
        await on_response_received
        return on_response_received.result()
    finally:
        transport.close()


class InverterError(Exception):
    """Indicates error communicating with inverter"""


class DiscoveryError(Exception):
    """Raised when unable to discover inverter"""


InverterResponse = namedtuple("InverterResponse", "data, serial_number, type, sofware_version")


class Inverter:
    """Base wrapper around Inverter UDP protocol"""

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def get_model(self):
        """Request the model information from the inverter"""
        try:
            data = await self._make_model_request(self.host, self.port)
        except ValueError as ex:
            msg = "Received invalid data from inverter"
            raise InverterError(msg, str(self.__class__.__name__)) from ex
        return data

    async def get_data(self):
        """Request the runtime data from the inverter"""
        try:
            data = await self._make_request(self.host, self.port)
        except ValueError as ex:
            msg = "Received invalid data from inverter"
            raise InverterError(msg, str(self.__class__.__name__)) from ex
        return data

    @classmethod
    async def _make_model_request(cls, host, port):
        """
        Return instance of 'InverterResponse'
        Raise exception if unable to get version
        """
        raise NotImplementedError()

    @classmethod
    async def _make_request(cls, host, port):
        """
        Return instance of 'InverterResponse'
        Raise exception if unable to get data
        """
        raise NotImplementedError()

    @classmethod
    def sensors(cls):
        """
        Return sensor map
        """
        raise NotImplementedError()

    @staticmethod
    def _map_response(resp_data, sensors):
        """Process the response data and return dictionary with runtime values"""
        return {
            name: fn(resp_data, offset)
            for (offset, fn, _, name, _) in sensors
        }


async def discover(host, port=8899):
    """Contact the inverter at the specified value and answer appropriare Inverter instance"""
    failures = []
    for inverter in REGISTRY:
        i = inverter(host, port)
        try:
            _LOGGER.debug("Probing %s inverter at %s:%s", inverter.__name__, host, port)
            response = await i.get_model()
            _LOGGER.debug("Detected %s inverter %s, S/N:%s", inverter.__name__, response.type, response.serial_number)
            return i
        except asyncio.exceptions.CancelledError as ex:
            failures.append(ex)
        except InverterError as ex:
            failures.append(ex)
    msg = (
        "Unable to connect to the inverter at "
        f"host={host} port={port}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )
    raise DiscoveryError(msg)


class ET(Inverter):
    """Class representing inverter of ET family"""

    # (request data including checksum, expected response length)
    _READ_DEVICE_VERSION_INFO = (
        bytes((0xF7, 0x03, 0x88, 0xB8, 0x00, 0x21, 0x3A, 0xC1)),
        (73,),
    )
    _READ_DEVICE_RUNNING_DATA1 = (
        bytes((0xF7, 0x03, 0x89, 0x1C, 0x00, 0x7D, 0x7A, 0xE7)),
        (257,),
    )
    _READ_BATTERY_INFO = (bytes((0xF7, 0x03, 0x90, 0x88, 0x00, 0x0B, 0xBD, 0xB1)), (29,))

    __model_name = None
    __serial_number = None
    __software_version = None

    # Sensors ("id, offset, getter, unit, name, icon")
    __sensors = (
        (6, _read_voltage, "V", "PV1 Voltage", _ICON_PV),
        (8, _read_current, "A", "PV1 Current", _ICON_PV),
        (10, _read_power, "W", "PV1 Power", _ICON_PV),
        (14, _read_voltage, "V", "PV2 Voltage", _ICON_PV),
        (16, _read_current, "A", "PV2 Current", _ICON_PV),
        (18, _read_power, "W", "PV2 Power", _ICON_PV),
        #(22, _read_voltage, "V", "PV3 Voltage", _ICON_PV),
        #(24, _read_current, "A", "PV3 Current", _ICON_PV),
        #(26, _read_power, "W", "PV3 Power", _ICON_PV),
        #(30, _read_voltage, "V", "PV4 Voltage", _ICON_PV),
        #(32, _read_current, "A", "PV4 Current", _ICON_PV),
        #(34, _read_power, "W", "PV4 Power", _ICON_PV),
        # 'PV Power': ppv1 + ppv2 + ppv3 + ppv4
        (
            -10,
            lambda data, x: _read_power(data, 10) + _read_power(data, 18),
            "W", "PV Power", _ICON_PV,
        ),
        (42, _read_voltage, "V", "On-grid 1 Voltage", _ICON_AC),
        (44, _read_current, "A", "On-grid Current", _ICON_AC),
        (46, _read_freq, "Hz", "On-grid Frequency", _ICON_AC),
        (48, _read_power, "W", "On-grid Power", _ICON_AC),
        (52, _read_voltage, "V", "On-grid2 Voltage", _ICON_AC),
        (54, _read_current, "A", "On-grid2 Current", _ICON_AC),
        (56, _read_freq, "Hz", "On-grid2 Frequency", _ICON_AC),
        (58, _read_power, "W", "On-grid2 Power", _ICON_AC),
        (62, _read_voltage, "V", "On-grid3 Voltage", _ICON_AC),
        (64, _read_current, "A", "On-grid3 Current", _ICON_AC),
        (66, _read_freq, "Hz", "On-grid3 Frequency", _ICON_AC),
        (68, _read_power, "W", "On-grid3 Power", _ICON_AC),
        (74, _read_power, "W", "Total Power", _ICON_AC),
        (78, _read_power, "W", "Active Power", _ICON_AC),
        #(-78, _read_grid_mode, "", "On-grid Mode",  _ICON_AC),
        (90, _read_voltage, "V", "Back-up1 Voltage", _ICON_AC_BACK),
        (92, _read_current, "A", "Back-up1 Current", _ICON_AC_BACK),
        (94, _read_freq, "Hz", "Back-up1 Frequency", _ICON_AC_BACK),
        #(96, _read_bytes2, "", "Back-up1 ?", None);
        (98, _read_power, "W", "Back-up1 Power", _ICON_AC_BACK),
        (102, _read_voltage, "V", "Back-up2 Voltage", _ICON_AC_BACK),
        (104, _read_current, "A", "Back-up2 Current", _ICON_AC_BACK),
        (106, _read_freq, "Hz", "Back-up2 Frequency", _ICON_AC_BACK),
        #(108, _read_bytes2, "", 'Back-up2 ?', None);
        (110, _read_power, "W", "Back-up2 Power", _ICON_AC_BACK),
        (114, _read_voltage, "V", "Back-up3 Voltage", _ICON_AC_BACK),
        (116, _read_current, "A", "Back-up3 Current", _ICON_AC_BACK),
        (118, _read_freq, "Hz", "Back-up3 Frequency", _ICON_AC_BACK),
        #(120, _read_bytes2, "", 'Back-up3 ?', None);
        (122, _read_power, "W", "Back-up3 Power", _ICON_AC_BACK),
        (126, _read_power, "W", "Load 1", _ICON_AC),
        (130, _read_power, "W", "Load 2", _ICON_AC),
        (134, _read_power, "W", "Load 3", _ICON_AC),
        # 'Load Total': load_p1 + load_p2 + load_p3
        (
            -126,
            lambda data, x: _read_power(data, 126)
            + _read_power(data, 130)
            + _read_power(data, 134),
            "W", "Load Total", _ICON_AC,
        ),
        (138, _read_power, "W", "Back-up Power", _ICON_AC_BACK),
        (142, _read_power, "W", "Load", _ICON_AC),
        (160, _read_voltage, "V", "Battery Voltage", _ICON_BATT),
        (162, _read_current, "A", "Battery Current", _ICON_BATT),
        # 'Battery Power': round('Battery Voltage' * 'Battery Current', 'W'),
        (
            -160,
            lambda data, x: round(_read_voltage(data, 160) * _read_current(data, 162)),
            "W", "Battery Power", _ICON_BATT,
        ),
        (168, _read_battery_mode, "", "Battery Mode", _ICON_BATT),
        (172, _read_safety_country, "", "Safety Country", None),
        (174, _read_work_mode, "", "Work Mode", None),
        (178, _read_bytes4, "", "Error Codes", None),
        (182, _read_power_k, "kW", "Total Energy", None),
        (186, _read_power_k, "kW", "Today's Energy", None),
        (240, _read_bytes4, "", "Diag Status", None),
    )

    __sensors_battery = (
        (1000, _read_bytes2, "", "Battery BMS", _ICON_BATT),
        (1002, _read_bytes2, "", "Battery Index", _ICON_BATT),
        (1006, _read_temp, "C", "Battery Temperature", _ICON_BATT),
        (1008, _read_bytes2, "A", "Battery Charge Limit", _ICON_BATT),
        (1010, _read_bytes2, "A", "Battery Discharge Limit", _ICON_BATT),
        (1012, _read_bytes2, "", "Battery Status", _ICON_BATT),
        (1014, _read_bytes2, "%", "Battery State of Charge", _ICON_BATT),
        (1016, _read_bytes2, "%", "Battery State of Health", _ICON_BATT),
        (1020, _read_bytes2, "", "Battery Warning", None),
    )

    @classmethod
    async def _make_model_request(cls, host, port):
        response = await _read_from_socket(cls._READ_DEVICE_VERSION_INFO, (host, port))
        if response is not None:
            response = response[5:-2]
            cls.__serial_number = response[6:22].decode("utf-8")
            cls.__model_name = response[22:32].decode("utf-8")
            cls.__software_version = response[54:66].decode("utf-8")
            return InverterResponse(
                data=None, serial_number=cls.__serial_number, type=cls.__model_name, sofware_version=cls.__software_version
            )
        else:
            raise ValueError

    @classmethod
    async def _make_request(cls, host, port):
        raw_data = await _read_from_socket(cls._READ_DEVICE_RUNNING_DATA1, (host, port))
        data = cls._map_response(raw_data[5:-2], cls.__sensors)
        raw_data = await _read_from_socket(cls._READ_BATTERY_INFO, (host, port))
        data.update(cls._map_response(raw_data[5:-2], cls.__sensors_battery))
        return InverterResponse(
            data=data, serial_number=cls.__serial_number, type=cls.__model_name, sofware_version=cls.__software_version
        )

    @classmethod
    def sensors(cls):
        return cls.__sensors + cls.__sensors_battery


class ES(Inverter):
    """Class representing inverter of ES family"""

    # (request data including checksum, expected response length)
    _READ_DEVICE_VERSION_INFO = (
        bytes((0xAA, 0x55, 0xC0, 0x7F, 0x01, 0x02, 0x00, 0x02, 0x41)),
        (85,86),
    )
    _READ_DEVICE_RUNNING_DATA = (
        bytes((0xAA, 0x55, 0xC0, 0x7F, 0x01, 0x06, 0x00, 0x02, 0x45)),
        (142,149),
    )

    __model_name = None
    __serial_number = None
    __software_version = None

    # Sensors ("id, offset, getter, unit, name, icon")
    __sensors = (
        (0, _read_voltage, "V", "PV1 Voltage", _ICON_PV),
        (2, _read_current, "A", "PV1 Current", _ICON_PV),
        (
            -2,
            lambda data, x: round(_read_voltage(data, 0) * _read_current(data, 2)),
            "W", "PV1 Power", _ICON_PV,
        ),
        (4, _read_pv_mode1, "", "PV1 Mode", _ICON_PV),
        (5, _read_voltage, "V", "PV2 Voltage", _ICON_PV),
        (7, _read_current, "A", "PV2 Current", _ICON_PV),
        (
            -7,
            lambda data, x: round(_read_voltage(data, 5) * _read_current(data, 7)),
            "W", "PV2 Power", _ICON_PV,
        ),
        (9, _read_pv_mode1, "", "PV2 Mode", _ICON_PV),
        (
            -9,
            lambda data, x: round(_read_voltage(data, 0) * _read_current(data, 2)) + round(_read_voltage(data, 5) * _read_current(data, 7)),
            "W", "PV Power", _ICON_PV,
        ),
        (10, _read_voltage, "V", "Battery Voltage", _ICON_BATT),
        (12, _read_voltage, "V", "Battery Voltage 2", _ICON_BATT),
        (14, _read_voltage, "V", "Battery Voltage 3", _ICON_BATT),
        (16, _read_voltage, "V", "Battery Voltage 4", _ICON_BATT),
        (18, _read_current, "A", "Battery Current", _ICON_BATT),
        (20, _read_bytes2, "A", "Battery Charge Limit", _ICON_BATT),
        (22, _read_bytes2, "A", "Battery Discharge Limit", _ICON_BATT),
        # BMS status 24-25
        (26, _read_byte, "%", "Battery State of Charge", _ICON_BATT),
        (27, _read_byte, "%", "Battery State of Charge 2", _ICON_BATT),
        (28, _read_byte, "%", "Battery State of Charge 3", _ICON_BATT),
        (29, _read_byte, "%", "Battery State of Health", _ICON_BATT),
        (30, _read_battery_mode1, "", "Battery Mode", _ICON_BATT),
        # BMS warning 31-32
        # Meter status 33
        (34, _read_voltage, "V", "On-grid Voltage", _ICON_AC),
        (36, _read_current, "A", "On-grid Current", _ICON_AC),
        (38, _read_power2, "W", "On-grid Power", _ICON_AC),
        (40, _read_freq, "Hz", "On-grid Frequency", _ICON_AC),
        (41, _read_work_mode1, "", "Work Mode", None),
        (43, _read_voltage, "V", "Back-up Voltage", _ICON_AC_BACK),
        (45, _read_current, "A", "Back-up Current", _ICON_AC_BACK),
        (47, _read_power2, "W", "Back-up Power", _ICON_AC_BACK),
        (49, _read_freq, "Hz", "Back-up Frequency", _ICON_AC_BACK),
        (51, _read_load_mode1, "", "Load Mode", None),
        (52, _read_energy_mode1, "", "Energy Mode", None),
        (53, _read_temp, "C", "Inverter Temperature", None),
        (55, _read_bytes4, "", "Error Codes", None),
        (59, _read_power_k, "kW", "Total Energy", None),
        # htotal 63-66
        (67, _read_power_k2, "kW", "Today's Energy", None),
        (69, _read_power_k2, "kW", "Today's Load", None),
        (71, _read_power_k, "kW", "Total Load", None),
        (75, _read_bytes2, "kW", "Total Power", None),
        # Effective work mode 77
        # Effective relay control 78-79
        (80, _read_grid_mode1, '', 'On-grid Mode', None),
        (89, _read_bytes4, "", "Diag Status", None),
    )

    @classmethod
    async def _make_model_request(cls, host, port):
        response = await _read_from_socket(cls._READ_DEVICE_VERSION_INFO, (host, port))
        if response is not None:
            cls.__serial_number = response[38:54].decode("utf-8")
            cls.__model_name = response[12:22].decode("utf-8")
            cls.__software_version = response[58:70].decode("utf-8")
            return InverterResponse(
                data=None, serial_number=cls.__serial_number, type=cls.__model_name, sofware_version=cls.__software_version
            )
        else:
            raise ValueError

    @classmethod
    async def _make_request(cls, host, port):
        raw_data = await _read_from_socket(cls._READ_DEVICE_RUNNING_DATA, (host, port))
        data = cls._map_response(raw_data[7:-2], cls.__sensors)
        return InverterResponse(
            data=data, serial_number=cls.__serial_number, type=cls.__model_name, sofware_version=cls.__software_version
        )

    @classmethod
    def sensors(cls):
        return cls.__sensors

# registry of supported inverter models
REGISTRY = [ET, ES]
