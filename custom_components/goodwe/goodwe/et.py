from typing import Any, Tuple

from .inverter import Inverter, Sensor
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand
from .utils import *


class ET(Inverter):
    """Class representing inverter of ET family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusReadCommand(0x88b8, 0x0021, 73)
    _READ_DEVICE_RUNNING_DATA1: ProtocolCommand = ModbusReadCommand(0x891c, 0x007d, 257)
    _READ_DEVICE_RUNNING_DATA2: ProtocolCommand = ModbusReadCommand(0x8ca0, 0x0011, 41)
    _READ_BATTERY_INFO: ProtocolCommand = ModbusReadCommand(0x9088, 0x000b, 29)
    _GET_WORK_MODE: ProtocolCommand = ModbusReadCommand(0xb798, 0x0001, 9)
    _READ_ETU_ADVANCED_PARAM1: ProtocolCommand = ModbusReadCommand(0xb98c, 0x000b, 29)
    _READ_ETU_ADVANCED_PARAM2: ProtocolCommand = ModbusReadCommand(0xb0c3, 0x0001, 0)
    _READ_ETU_ADVANCED_PARAM3: ProtocolCommand = ModbusReadCommand(0xb0c0, 0x0007, 21)
    _READ_ETU_ADVANCED_PARAM4: ProtocolCommand = ModbusReadCommand(0xb1aa, 0x0001, 9)
    _READ_ETU_ADVANCED_PARAM5: ProtocolCommand = ModbusReadCommand(0xb126, 0x000a, 27)
    _READ_ETU_BATTERY_SOC_SWITCH: ProtocolCommand = ModbusReadCommand(0xb98c, 0x0001, 9)

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 6, read_voltage, "V", "PV1 Voltage", Kind.PV),
        Sensor("ipv1", 8, read_current, "A", "PV1 Current", Kind.PV),
        Sensor("ppv1", 10, read_power, "W", "PV1 Power", Kind.PV),
        Sensor("vpv2", 14, read_voltage, "V", "PV2 Voltage", Kind.PV),
        Sensor("ipv2", 16, read_current, "A", "PV2 Current", Kind.PV),
        Sensor("ppv2", 18, read_power, "W", "PV2 Power", Kind.PV),
        # Sensor("vpv3", 22, read_voltage, "V", "PV3 Voltage", Kind.PV),
        # Sensor("ipv3", 24, read_current, "A", "PV3 Current", Kind.PV),
        # Sensor("ppv3", 26, read_power, "W", "PV3 Power", Kind.PV),
        # Sensor("vpv4", 30, read_voltage, "V", "PV4 Voltage", Kind.PV),
        # Sensor("ipv4", 32, read_current, "A", "PV4 Current", Kind.PV),
        # Sensor("ppv4", 34, read_power, "W", "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Sensor("ppv", 0, lambda data, _: read_power(data, 10) + read_power(data, 18), "W", "PV Power", Kind.PV),
        Sensor("xx38", 38, read_bytes2, "", "Unknown sensor@38", None),
        Sensor("xx40", 40, read_bytes2, "", "Unknown sensor@40", None),
        Sensor("vgrid", 42, read_voltage, "V", "On-grid L1 Voltage", Kind.AC),
        Sensor("igrid", 44, read_current, "A", "On-grid L1 Current", Kind.AC),
        Sensor("fgrid", 46, read_freq, "Hz", "On-grid L1 Frequency", Kind.AC),
        Sensor("pgrid", 48, read_power, "W", "On-grid L1 Power", Kind.AC),
        Sensor("vgrid2", 52, read_voltage, "V", "On-grid L2 Voltage", Kind.AC),
        Sensor("igrid2", 54, read_current, "A", "On-grid L2 Current", Kind.AC),
        Sensor("fgrid2", 56, read_freq, "Hz", "On-grid L2 Frequency", Kind.AC),
        Sensor("pgrid2", 58, read_power, "W", "On-grid L2 Power", Kind.AC),
        Sensor("vgrid3", 62, read_voltage, "V", "On-grid L3 Voltage", Kind.AC),
        Sensor("igrid3", 64, read_current, "A", "On-grid L3 Current", Kind.AC),
        Sensor("fgrid3", 66, read_freq, "Hz", "On-grid L3 Frequency", Kind.AC),
        Sensor("pgrid3", 68, read_power, "W", "On-grid L3 Power", Kind.AC),
        Sensor("xx72", 72, read_bytes2, "", "Unknown sensor@72", None),
        Sensor("total_inverter_power", 74, read_power, "W", "Total Power", Kind.AC),
        Sensor("active_power", 78, read_power, "W", "Active Power", Kind.AC),
        Sensor("grid_in_out", 78, read_grid_mode, "", "On-grid Mode code", Kind.AC),
        Sensor("grid_in_out_label", 0, lambda data, _: GRID_MODES.get(read_grid_mode(data, 78)), "", "On-grid Mode",
               Kind.AC),
        Sensor("xx82", 82, read_bytes2, "", "Unknown sensor@82", None),
        Sensor("xx84", 84, read_bytes2, "", "Unknown sensor@84", None),
        Sensor("xx86", 86, read_bytes2, "", "Unknown sensor@86", None),
        Sensor("backup_v1", 90, read_voltage, "V", "Back-up L1 Voltage", Kind.UPS),
        Sensor("backup_i1", 92, read_current, "A", "Back-up L1 Current", Kind.UPS),
        Sensor("backup_f1", 94, read_freq, "Hz", "Back-up L1 Frequency", Kind.UPS),
        Sensor("xx96", 96, read_bytes2, "", "Unknown sensor@96", None),
        Sensor("backup_p1", 98, read_power, "W", "Back-up L1 Power", Kind.UPS),
        Sensor("backup_v2", 102, read_voltage, "V", "Back-up L2 Voltage", Kind.UPS),
        Sensor("backup_i2", 104, read_current, "A", "Back-up L2 Current", Kind.UPS),
        Sensor("backup_f2", 106, read_freq, "Hz", "Back-up L2 Frequency", Kind.UPS),
        Sensor("xx108", 108, read_bytes2, "", "Unknown sensor@108", None),
        Sensor("backup_p2", 110, read_power, "W", "Back-up L2 Power", Kind.UPS),
        Sensor("backup_v3", 114, read_voltage, "V", "Back-up L3 Voltage", Kind.UPS),
        Sensor("backup_i3", 116, read_current, "A", "Back-up L3 Current", Kind.UPS),
        Sensor("backup_f3", 118, read_freq, "Hz", "Back-up L3 Frequency", Kind.UPS),
        Sensor("xx120", 120, read_bytes2, "", "Unknown sensor@120", None),
        Sensor("backup_p3", 122, read_power, "W", "Back-up L3 Power", Kind.UPS),
        Sensor("load_p1", 126, read_power, "W", "Load L1", Kind.AC),
        Sensor("load_p2", 130, read_power, "W", "Load L2", Kind.AC),
        Sensor("load_p3", 134, read_power, "W", "Load L3", Kind.AC),
        # load_p1 + load_p2 + load_p3
        Sensor("load_ptotal", 0,
               lambda data, _: read_power(data, 126) + read_power(data, 130) + read_power(data, 134),
               "W", "Load Total", Kind.AC),
        Sensor("backup_ptotal", 138, read_power, "W", "Back-up Power", Kind.UPS),
        Sensor("pload", 142, read_power, "W", "Load", Kind.AC),
        Sensor("xx146", 146, read_bytes2, "", "Unknown sensor@146", None),
        Sensor("temperature2", 148, read_temp, "C", "Inverter Temperature 2", Kind.AC),
        Sensor("xx150", 150, read_bytes2, "", "Unknown sensor@150", None),
        Sensor("temperature", 152, read_temp, "C", "Inverter Temperature", Kind.AC),
        Sensor("xx154", 154, read_bytes2, "", "Unknown sensor@154", None),
        Sensor("xx156", 156, read_bytes2, "", "Unknown sensor@156", None),
        Sensor("xx158", 158, read_bytes2, "", "Unknown sensor@158", None),
        Sensor("vbattery1", 160, read_voltage, "V", "Battery Voltage", Kind.BAT),
        Sensor("ibattery1", 162, read_current, "A", "Battery Current", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Sensor("pbattery1", 0,
               lambda data, _: round(read_voltage(data, 160) * read_current(data, 162)),
               "W", "Battery Power", Kind.BAT),
        Sensor("battery_mode", 168, read_bytes2, "", "Battery Mode code", Kind.BAT),
        Sensor("battery_mode_label", 168, read_battery_mode, "", "Battery Mode", Kind.BAT),
        Sensor("xx170", 170, read_bytes2, "", "Unknown sensor@170", None),
        Sensor("safety_country", 172, read_bytes2, "", "Safety Country code", Kind.AC),
        Sensor("safety_country_label", 172, read_safety_country, "", "Safety Country", Kind.AC),
        Sensor("work_mode", 174, read_bytes2, "", "Work Mode code", None),
        Sensor("work_mode_label", 174, read_work_mode_et, "", "Work Mode", None),
        Sensor("xx176", 176, read_bytes2, "", "Unknown sensor@176", None),
        Sensor("error_codes", 178, read_bytes4, "", "Error Codes", None),
        Sensor("e_total", 182, read_power_k, "kWh", "Total PV Generation", Kind.PV),
        Sensor("e_day", 186, read_power_k, "kWh", "Today's PV Generation", Kind.PV),
        Sensor("xx190", 190, read_bytes2, "", "Unknown sensor@190", None),
        Sensor("s_total", 192, read_power_k2, "kWh", "Total Electricity Sold", Kind.AC),
        Sensor("h_total", 194, read_bytes4, "", "Hours Total", Kind.PV),
        Sensor("xx198", 198, read_bytes2, "", "Unknown sensor@198", None),
        Sensor("s_day", 200, read_power_k2, "kWh", "Today Electricity Sold", Kind.AC),
        Sensor("diagnose_result", 240, read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - active_power
        Sensor("house_consumption", 0,
               lambda data, _: read_power(data, 10) + read_power(data, 18) + round(
                   read_voltage(data, 160) * read_current(data, 162)) - read_power(data, 78),
               "W", "House Comsumption", Kind.AC),
    )

    __sensors_battery: Tuple[Sensor, ...] = (
        Sensor("battery_bms", 0, read_bytes2, "", "Battery BMS", Kind.BAT),
        Sensor("battery_index", 2, read_bytes2, "", "Battery Index", Kind.BAT),
        Sensor("battery_temperature", 6, read_temp, "C", "Battery Temperature", Kind.BAT, ),
        Sensor("battery_charge_limit", 8, read_bytes2, "A", "Battery Charge Limit", Kind.BAT),
        Sensor("battery_discharge_limit", 10, read_bytes2, "A", "Battery Discharge Limit", Kind.BAT),
        Sensor("battery_status", 12, read_bytes2, "", "Battery Status", Kind.BAT),
        Sensor("battery_soc", 14, read_bytes2, "%", "Battery State of Charge", Kind.BAT),
        Sensor("battery_soh", 16, read_bytes2, "%", "Battery State of Health", Kind.BAT),
        Sensor("battery_warning", 20, read_bytes2, "", "Battery Warning", Kind.BAT),
    )

    __sensors2: Tuple[Sensor, ...] = (
        Sensor("xxx0", 0, read_bytes2, "", "Unknown sensor2@0", None),
        Sensor("xxx2", 2, read_bytes2, "", "Unknown sensor2@2", None),
        Sensor("xxx4", 4, read_bytes2, "", "Unknown sensor2@4", None),
        Sensor("xxx6", 6, read_bytes2, "", "Unknown sensor2@6", None),
        Sensor("xxx8", 8, read_bytes2, "", "Unknown sensor2@8", None),
        Sensor("xxx10", 10, read_bytes2, "", "Unknown sensor2@10", None),
        Sensor("xxx12", 12, read_bytes2, "", "Unknown sensor2@12", None),
        Sensor("xxx14", 14, read_bytes2, "", "Unknown sensor2@14", None),
        Sensor("xxx16", 16, read_bytes2, "", "Unknown sensor2@16", None),
        Sensor("xxx18", 18, read_bytes2, "", "Unknown sensor2@18", None),
        Sensor("xxx20", 20, read_bytes2, "", "Unknown sensor2@20", None),
        Sensor("xxx22", 22, read_bytes2, "", "Unknown sensor2@22", None),
        Sensor("xxx24", 24, read_bytes2, "", "Unknown sensor2@24", None),
        Sensor("xxx26", 26, read_bytes2, "", "Unknown sensor2@26", None),
        Sensor("xxx28", 28, read_bytes2, "", "Unknown sensor2@28", None),
        Sensor("xxx30", 30, read_bytes2, "", "Unknown sensor2@30", None),
        Sensor("xxx32", 32, read_bytes2, "", "Unknown sensor2@32", None),
    )

    __params1: Tuple[Sensor, ...] = (
        Sensor("switchBackflowLimit", 18, read_bytes2, "", "Back-flow enabled", None),
        Sensor("backflowLimit", 18, read_bytes2, "", "Back-flow limit", None),
    )

    __params3: Tuple[Sensor, ...] = (
        Sensor("switchColdStart", 0, read_bytes2, "", "Cold start", None),
        Sensor("switchShadowscan", 6, read_bytes2, "", "Shadow scan", None),
        Sensor("switchBackup", 8, read_bytes2, "", "Backup enabled", None),
        Sensor("sensitivityCheck", 12, read_bytes2, "", "Sensitivity check mode", None),
    )

    __params4: Tuple[Sensor, ...] = (
        # TODO convert this to float ??
        Sensor("powerFactor", 0, read_bytes2, "", "Power Factor", None),
    )

    __params5: Tuple[Sensor, ...] = (
        Sensor("batteryCapacity", 0, read_bytes2, "", "Battery capacity", None),
        Sensor("batteryNumber", 2, read_bytes2, "", "Battery count", None),
        Sensor("batteryChargeVoltage", 4, read_voltage, "", "Battery charge voltage", None),
        Sensor("batteryChargeCurrent", 6, read_current, "", "Battery charge current", None),
        Sensor("batteryDischargeVoltage", 8, read_voltage, "", "Battery discharge voltage", None),
        Sensor("batteryDischargeCurrent", 10, read_current, "", "Battery discharge current", None),
        Sensor("batteryDischargeDepth", 12, read_bytes2, "", "Battery discharge depth", None),
        Sensor("batteryOfflineDischargeDepth", 16, read_bytes2, "", "Battery discharge depth (off-line)", None),
    )

    __soc_switch: Tuple[Sensor, ...] = (
        Sensor("batterySocSwitch", 0, read_bytes2, "", "Battery SoC Switch", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.serial_number = response[6:22].decode("ascii")
        self.software_version = response[54:66].decode("ascii")

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA1)
        data = self._map_response(raw_data[5:-2], self.__sensors, include_unknown_sensors)
        raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
        data.update(self._map_response(raw_data[5:-2], self.__sensors_battery, include_unknown_sensors))
        if include_unknown_sensors:  # all sensors in RUNNING_DATA2 request are not yet know at the moment
            raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA2)
            data.update(self._map_response(raw_data[5:-2], self.__sensors2, include_unknown_sensors))
        return data

    async def read_settings_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_ETU_ADVANCED_PARAM1)
        data = self._map_response(raw_data[5:-2], self.__params1)
        raw_data = await self._read_from_socket(self._READ_ETU_ADVANCED_PARAM3)
        data.update(self._map_response(raw_data[5:-2], self.__params3))
        raw_data = await self._read_from_socket(self._READ_ETU_ADVANCED_PARAM4)
        data.update(self._map_response(raw_data[5:-2], self.__params4))
        raw_data = await self._read_from_socket(self._READ_ETU_ADVANCED_PARAM5)
        data.update(self._map_response(raw_data[5:-2], self.__params5))
        raw_data = await self._read_from_socket(self._READ_ETU_BATTERY_SOC_SWITCH)
        data.update(self._map_response(raw_data[5:-2], self.__soc_switch))
        return data

    async def set_work_mode(self, work_mode: int):
        if work_mode in (0, 1, 2):
            await self._read_from_socket(ModbusWriteCommand(0xb798, work_mode))

    async def set_ongrid_battery_dod(self, dod: int):
        if 0 <= dod <= 89:
            await self._read_from_socket(ModbusWriteCommand(0xb12c, 100 - dod, 10))

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors + cls.__sensors_battery + cls.__sensors2

    @classmethod
    def settings(cls) -> Tuple[Sensor, ...]:
        return cls.__params1 + cls.__params3 + cls.__params4 + cls.__params5 + cls.__soc_switch
