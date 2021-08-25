from typing import Any, Tuple

from .inverter import Inverter, Sensor
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusProtocolCommand
from .utils import *


class DT(Inverter):
    """Class representing inverter of DT, D-NS and XS families"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusProtocolCommand("7F0375310028", 87)
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = ModbusProtocolCommand("7F0375940049", 153)

    __sensors: Tuple[Sensor, ...] = (
        Sensor("timestamp", 0, read_datetime, "", "Timestamp", None),
        Sensor("vpv1", 6, read_voltage, "V", "PV1 Voltage", Kind.PV),
        Sensor("ipv1", 8, read_current, "A", "PV1 Current", Kind.PV),
        Sensor("ppv1", 0,
               lambda data, _: round(read_voltage(data, 6) * read_current(data, 8)),
               "W", "PV1 Power", Kind.PV),
        Sensor("vpv2", 10, read_voltage, "V", "PV2 Voltage", Kind.PV),
        Sensor("ipv2", 12, read_current, "A", "PV2 Current", Kind.PV),
        Sensor("ppv2", 0,
               lambda data, _: round(read_voltage(data, 10) * read_current(data, 12)),
               "W", "PV2 Power", Kind.PV),
        Sensor("xx14", 14, read_bytes2, "", "Unknown sensor@14", None),
        Sensor("xx16", 16, read_bytes2, "", "Unknown sensor@16", None),
        Sensor("xx18", 18, read_bytes2, "", "Unknown sensor@18", None),
        Sensor("xx20", 20, read_bytes2, "", "Unknown sensor@20", None),
        Sensor("xx22", 22, read_bytes2, "", "Unknown sensor@22", None),
        Sensor("xx24", 24, read_bytes2, "", "Unknown sensor@24", None),
        Sensor("xx26", 26, read_bytes2, "", "Unknown sensor@26", None),
        Sensor("xx28", 28, read_bytes2, "", "Unknown sensor@28", None),
        Sensor("vline1", 30, read_voltage, "V", "On-grid L1-L2 Voltage", Kind.AC),
        Sensor("vline2", 32, read_voltage, "V", "On-grid L2-L3 Voltage", Kind.AC),
        Sensor("vline3", 34, read_voltage, "V", "On-grid L3-L1 Voltage", Kind.AC),
        Sensor("vgrid1", 36, read_voltage, "V", "On-grid L1 Voltage", Kind.AC),
        Sensor("vgrid2", 38, read_voltage, "V", "On-grid L2 Voltage", Kind.AC),
        Sensor("vgrid3", 40, read_voltage, "V", "On-grid L3 Voltage", Kind.AC),
        Sensor("igrid1", 42, read_current, "A", "On-grid L1 Current", Kind.AC),
        Sensor("igrid2", 44, read_current, "A", "On-grid L2 Current", Kind.AC),
        Sensor("igrid3", 46, read_current, "A", "On-grid L3 Current", Kind.AC),
        Sensor("fgrid1", 48, read_freq, "Hz", "On-grid L1 Frequency", Kind.AC),
        Sensor("fgrid2", 50, read_freq, "Hz", "On-grid L2 Frequency", Kind.AC),
        Sensor("fgrid3", 52, read_freq, "Hz", "On-grid L3 Frequency", Kind.AC),
        Sensor("pgrid1", 0,
               lambda data, _: round(read_voltage(data, 36) * read_current(data, 42)),
               "W", "On-grid L1 Power", Kind.AC),
        Sensor("pgrid2", 0,
               lambda data, _: round(read_voltage(data, 38) * read_current(data, 44)),
               "W", "On-grid L2 Power", Kind.AC),
        Sensor("pgrid3", 0,
               lambda data, _: round(read_voltage(data, 40) * read_current(data, 46)),
               "W", "On-grid L3 Power", Kind.AC),
        Sensor("xx54", 54, read_bytes2, "", "Unknown sensor@54", None),
        Sensor("ppv", 56, read_power2, "W", "PV Power", Kind.PV),
        Sensor("work_mode", 58, read_bytes2, "", "Work Mode code", None),
        Sensor("work_mode_label", 58, read_work_mode_dt, "", "Work Mode", None),
        Sensor("xx60", 60, read_bytes2, "", "Unknown sensor@60", None),
        Sensor("xx62", 62, read_bytes2, "", "Unknown sensor@62", None),
        Sensor("xx64", 64, read_bytes2, "", "Unknown sensor@64", None),
        Sensor("xx66", 66, read_bytes2, "", "Unknown sensor@66", None),
        Sensor("xx68", 68, read_bytes2, "", "Unknown sensor@68", None),
        Sensor("xx70", 70, read_bytes2, "", "Unknown sensor@70", None),
        Sensor("xx72", 72, read_bytes2, "", "Unknown sensor@72", None),
        Sensor("xx74", 74, read_bytes2, "", "Unknown sensor@74", None),
        Sensor("xx76", 76, read_bytes2, "", "Unknown sensor@76", None),
        Sensor("xx78", 78, read_bytes2, "", "Unknown sensor@78", None),
        Sensor("xx80", 80, read_bytes2, "", "Unknown sensor@80", None),
        Sensor("temperature", 82, read_temp, "C", "Inverter Temperature", Kind.AC),
        Sensor("xx84", 84, read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, read_bytes2, "", "Unknown sensor@86", None),
        Sensor("e_day", 88, read_power_k2, "kWh", "Today's PV Generation", Kind.PV),
        Sensor("xx90", 90, read_bytes2, "", "Unknown sensor@90", None),
        Sensor("e_total", 92, read_power_k2, "kWh", "Total PV Generation", Kind.PV),
        Sensor("xx94", 94, read_bytes2, "", "Unknown sensor@94", None),
        Sensor("h_total", 96, read_bytes2, "", "Hours Total", Kind.PV),
        Sensor("safety_country", 98, read_bytes2, "", "Safety Country code", Kind.AC),
        Sensor("safety_country_label", 98, read_safety_country, "", "Safety Country", Kind.AC),
        Sensor("xx100", 100, read_bytes2, "", "Unknown sensor@100", None),
        Sensor("xx102", 102, read_bytes2, "", "Unknown sensor@102", None),
        Sensor("xx104", 104, read_bytes2, "", "Unknown sensor@104", None),
        Sensor("xx106", 106, read_bytes2, "", "Unknown sensor@106", None),
        Sensor("xx108", 108, read_bytes2, "", "Unknown sensor@108", None),
        Sensor("xx110", 110, read_bytes2, "", "Unknown sensor@110", None),
        Sensor("xx112", 112, read_bytes2, "", "Unknown sensor@112", None),
        Sensor("xx114", 114, read_bytes2, "", "Unknown sensor@114", None),
        Sensor("xx116", 116, read_bytes2, "", "Unknown sensor@116", None),
        Sensor("xx118", 118, read_bytes2, "", "Unknown sensor@118", None),
        Sensor("xx120", 120, read_bytes2, "", "Unknown sensor@120", None),
        Sensor("xx122", 122, read_bytes2, "", "Unknown sensor@122", None),
        Sensor("funbit", 124, read_bytes2, "", "FunBit", Kind.PV),
        Sensor("vbus", 126, read_voltage, "V", "Bus Voltage", Kind.PV),
        Sensor("vnbus", 128, read_voltage, "V", "NBus Voltage", Kind.PV),
        Sensor("xx130", 130, read_bytes2, "", "Unknown sensor@130", None),
        Sensor("xx132", 132, read_bytes2, "", "Unknown sensor@132", None),
        Sensor("xx134", 134, read_bytes2, "", "Unknown sensor@134", None),
        Sensor("xx136", 136, read_bytes2, "", "Unknown sensor@136", None),
        Sensor("xx138", 138, read_bytes2, "", "Unknown sensor@138", None),
        Sensor("xx140", 140, read_bytes2, "", "Unknown sensor@140", None),
        Sensor("xx142", 142, read_bytes2, "", "Unknown sensor@142", None),
        Sensor("xx144", 144, read_bytes2, "", "Unknown sensor@144", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.software_version = "{}.{}.{:02x}".format(
            int.from_bytes(response[66:68], byteorder='big'),
            int.from_bytes(response[68:70], byteorder='big'),
            int.from_bytes(response[70:72], byteorder='big'),
        )

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self.__sensors, include_unknown_sensors)

        return data

    async def set_ongrid_battery_dod(self, dod: int):
        pass

    async def set_work_mode(self, work_mode: int):
        if work_mode == 0:
            await self._read_from_socket(ModbusProtocolCommand("7F069D8B0000"))
        elif work_mode == 3:
            await self._read_from_socket(ModbusProtocolCommand("7F069D8A0000"))

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors
