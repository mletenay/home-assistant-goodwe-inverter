from typing import Tuple

from .inverter import Inverter
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand
from .sensor import *


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
        Voltage("vpv1", 6, "PV1 Voltage", Kind.PV),
        Current("ipv1", 8, "PV1 Current", Kind.PV),
        Power4("ppv1", 10, "PV1 Power", Kind.PV),
        Voltage("vpv2", 14, "PV2 Voltage", Kind.PV),
        Current("ipv2", 16, "PV2 Current", Kind.PV),
        Power4("ppv2", 18, "PV2 Power", Kind.PV),
        # Voltage("vpv3", 22, "PV3 Voltage", Kind.PV),
        # Current("ipv3", 24, "PV3 Current", Kind.PV),
        # Power4("ppv3", 26, "PV3 Power", Kind.PV),
        # Voltage("vpv4", 30, "PV4 Voltage", Kind.PV),
        # Current("ipv4", 32, "PV4 Current", Kind.PV),
        # Power4("ppv4", 34, "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv", 0, lambda data, _: read_power(data, 10) + read_power(data, 18), "PV Power", "W", Kind.PV),
        Integer("xx38", 38, "Unknown sensor@38"),
        Integer("xx40", 40, "Unknown sensor@40"),
        Voltage("vgrid", 42, "On-grid L1 Voltage", Kind.AC),
        Current("igrid", 44, "On-grid L1 Current", Kind.AC),
        Frequency("fgrid", 46, "On-grid L1 Frequency", Kind.AC),
        Power4("pgrid", 48, "On-grid L1 Power", Kind.AC),
        Voltage("vgrid2", 52, "On-grid L2 Voltage", Kind.AC),
        Current("igrid2", 54, "On-grid L2 Current", Kind.AC),
        Frequency("fgrid2", 56, "On-grid L2 Frequency", Kind.AC),
        Power4("pgrid2", 58, "On-grid L2 Power", Kind.AC),
        Voltage("vgrid3", 62, "On-grid L3 Voltage", Kind.AC),
        Current("igrid3", 64, "On-grid L3 Current", Kind.AC),
        Frequency("fgrid3", 66, "On-grid L3 Frequency", Kind.AC),
        Power4("pgrid3", 68, "On-grid L3 Power", Kind.AC),
        Integer("xx72", 72, "Unknown sensor@72"),
        Power4("total_inverter_power", 74, "Total Power", Kind.AC),
        Power4("active_power", 78, "Active Power", Kind.AC),
        Calculated("grid_in_out", 78, lambda data, _: read_grid_mode(data, 78), "On-grid Mode code", "", Kind.AC),
        Calculated("grid_in_out_label", 0, lambda data, _: GRID_MODES.get(read_grid_mode(data, 78)), "On-grid Mode",
                   "", Kind.AC),
        Integer("xx82", 82, "Unknown sensor@82"),
        Integer("xx84", 84, "Unknown sensor@84"),
        Integer("xx86", 86, "Unknown sensor@86"),
        Voltage("backup_v1", 90, "Back-up L1 Voltage", Kind.UPS),
        Current("backup_i1", 92, "Back-up L1 Current", Kind.UPS),
        Frequency("backup_f1", 94, "Back-up L1 Frequency", Kind.UPS),
        Integer("xx96", 96, "Unknown sensor@96"),
        Power4("backup_p1", 98, "Back-up L1 Power", Kind.UPS),
        Voltage("backup_v2", 102, "Back-up L2 Voltage", Kind.UPS),
        Current("backup_i2", 104, "Back-up L2 Current", Kind.UPS),
        Frequency("backup_f2", 106, "Back-up L2 Frequency", Kind.UPS),
        Integer("xx108", 108, "Unknown sensor@108"),
        Power4("backup_p2", 110, "Back-up L2 Power", Kind.UPS),
        Voltage("backup_v3", 114, "Back-up L3 Voltage", Kind.UPS),
        Current("backup_i3", 116, "Back-up L3 Current", Kind.UPS),
        Frequency("backup_f3", 118, "Back-up L3 Frequency", Kind.UPS),
        Integer("xx120", 120, "Unknown sensor@120"),
        Power4("backup_p3", 122, "Back-up L3 Power", Kind.UPS),
        Power4("load_p1", 126, "Load L1", Kind.AC),
        Power4("load_p2", 130, "Load L2", Kind.AC),
        Power4("load_p3", 134, "Load L3", Kind.AC),
        # load_p1 + load_p2 + load_p3
        Calculated("load_ptotal", 0,
                   lambda data, _: read_power(data, 126) + read_power(data, 130) + read_power(data, 134),
                   "Load Total", "W", Kind.AC),
        Power4("backup_ptotal", 138, "Back-up Power", Kind.UPS),
        Power4("pload", 142, "Load", Kind.AC),
        Integer("xx146", 146, "Unknown sensor@146"),
        Temp("temperature2", 148, "Inverter Temperature 2", Kind.AC),
        Integer("xx150", 150, "Unknown sensor@150"),
        Temp("temperature", 152, "Inverter Temperature", Kind.AC),
        Integer("xx154", 154, "Unknown sensor@154"),
        Integer("xx156", 156, "Unknown sensor@156"),
        Integer("xx158", 158, "Unknown sensor@158"),
        Voltage("vbattery1", 160, "Battery Voltage", Kind.BAT),
        Current("ibattery1", 162, "Battery Current", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1", 0,
                   lambda data, _: round(read_voltage(data, 160) * read_current(data, 162)),
                   "Battery Power", "W", Kind.BAT),
        Integer("battery_mode", 168, "Battery Mode code", "", Kind.BAT),
        Enum2("battery_mode_label", 168, BATTERY_MODES_ET, "Battery Mode", "", Kind.BAT),
        Integer("xx170", 170, "Unknown sensor@170"),
        Integer("safety_country", 172, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 172, SAFETY_COUNTRIES_ET, "Safety Country", "", Kind.AC),
        Integer("work_mode", 174, "Work Mode code"),
        Enum2("work_mode_label", 174, WORK_MODES_ET, "Work Mode"),
        Integer("xx176", 176, "Unknown sensor@176"),
        Long("error_codes", 178, "Error Codes"),
        Energy4("e_total", 182, "Total PV Generation", Kind.PV),
        Energy4("e_day", 186, "Today's PV Generation", Kind.PV),
        Integer("xx190", 190, "Unknown sensor@190"),
        Energy("s_total", 192, "Total Electricity Sold", Kind.AC),
        Long("h_total", 194, "Hours Total", "h", Kind.PV),
        Integer("xx198", 198, "Unknown sensor@198"),
        Energy("s_day", 200, "Today Electricity Sold", Kind.AC),
        Long("diagnose_result", 240, "Diag Status"),
        # ppv1 + ppv2 + pbattery - active_power
        Calculated("house_consumption", 0,
                   lambda data, _: read_power(data, 10) + read_power(data, 18) + round(
                       read_voltage(data, 160) * read_current(data, 162)) - read_power(data, 78),
                   "House Comsumption", "W", Kind.AC),
    )

    __sensors_battery: Tuple[Sensor, ...] = (
        Integer("battery_bms", 0, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 2, "Battery Index", "", Kind.BAT),
        Temp("battery_temperature", 6, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 8, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 10, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_status", 12, "Battery Status", "", Kind.BAT),
        Integer("battery_soc", 14, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 16, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_warning", 20, "Battery Warning", "", Kind.BAT),
    )

    __sensors2: Tuple[Sensor, ...] = (
        Integer("xxx0", 0, "Unknown sensor2@0"),
        Integer("xxx2", 2, "Unknown sensor2@2"),
        Integer("xxx4", 4, "Unknown sensor2@4"),
        Integer("xxx6", 6, "Unknown sensor2@6"),
        Integer("xxx8", 8, "Unknown sensor2@8"),
        Integer("xxx10", 10, "Unknown sensor2@10"),
        Integer("xxx12", 12, "Unknown sensor2@12"),
        Integer("xxx14", 14, "Unknown sensor2@14"),
        Integer("xxx16", 16, "Unknown sensor2@16"),
        Integer("xxx18", 18, "Unknown sensor2@18"),
        Integer("xxx20", 20, "Unknown sensor2@20"),
        Integer("xxx22", 22, "Unknown sensor2@22"),
        Integer("xxx24", 24, "Unknown sensor2@24"),
        Integer("xxx26", 26, "Unknown sensor2@26"),
        Integer("xxx28", 28, "Unknown sensor2@28"),
        Integer("xxx30", 30, "Unknown sensor2@30"),
        Integer("xxx32", 32, "Unknown sensor2@32"),
    )

    __params1: Tuple[Sensor, ...] = (
        Integer("switchBackflowLimit", 18, "Back-flow enabled"),
        Integer("backflowLimit", 18, "Back-flow limit"),
    )

    __params3: Tuple[Sensor, ...] = (
        Integer("switchColdStart", 0, "Cold start"),
        Integer("switchShadowscan", 6, "Shadow scan"),
        Integer("switchBackup", 8, "Backup enabled"),
        Integer("sensitivityCheck", 12, "Sensitivity check mode"),
    )

    __params4: Tuple[Sensor, ...] = (
        # TODO convert this to float ??
        Integer("powerFactor", 0, "Power Factor"),
    )

    __params5: Tuple[Sensor, ...] = (
        Integer("batteryCapacity", 0, "Battery capacity", "", Kind.BAT),
        Integer("batteryNumber", 2, "Battery count", "", Kind.BAT),
        Voltage("batteryChargeVoltage", 4, "Battery charge voltage", Kind.BAT),
        Current("batteryChargeCurrent", 6, "Battery charge current", Kind.BAT),
        Voltage("batteryDischargeVoltage", 8, "Battery discharge voltage", Kind.BAT),
        Current("batteryDischargeCurrent", 10, "Battery discharge current", Kind.BAT),
        Integer("batteryDischargeDepth", 12, "Battery discharge depth", "%", Kind.BAT),
        Integer("batteryOfflineDischargeDepth", 16, "Battery discharge depth (off-line)", "%", Kind.BAT),
    )

    __soc_switch: Tuple[Sensor, ...] = (
        Integer("batterySocSwitch", 0, "Battery SoC Switch"),
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
