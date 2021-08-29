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

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __sensors: Tuple[Sensor, ...] = (
        Timestamp("timestamp", 0, "Timestamp"),
        Voltage("vpv1", 6, "PV1 Voltage", Kind.PV),
        Current("ipv1", 8, "PV1 Current", Kind.PV),
        Power4("ppv1", 10, "PV1 Power", Kind.PV),
        Voltage("vpv2", 14, "PV2 Voltage", Kind.PV),
        Current("ipv2", 16, "PV2 Current", Kind.PV),
        Power4("ppv2", 18, "PV2 Power", Kind.PV),
        # Voltage("vpv3", 22, "PV3 Voltage", Kind.PV), # modbus35111
        # Current("ipv3", 24, "PV3 Current", Kind.PV),
        # Power4("ppv3", 26, "PV3 Power", Kind.PV),
        # Voltage("vpv4", 30, "PV4 Voltage", Kind.PV),
        # Current("ipv4", 32, "PV4 Current", Kind.PV),
        # Power4("ppv4", 34, "PV4 Power", Kind.PV),
        # ppv1 + ppv2 + ppv3 + ppv4
        Calculated("ppv", 0, lambda data, _: read_power(data, 10) + read_power(data, 18), "PV Power", "W", Kind.PV),
        Integer("xx38", 38, "Unknown sensor@38"),
        Integer("xx40", 40, "Unknown sensor@40"),
        Voltage("vgrid", 42, "On-grid L1 Voltage", Kind.AC),  # modbus 35121
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
        Power4("reactive_power", 82, "Reactive Power", Kind.AC),
        Power4("apparent_power", 86, "Apparent Power", Kind.AC),
        Voltage("backup_v1", 90, "Back-up L1 Voltage", Kind.UPS),  # modbus 35145
        Current("backup_i1", 92, "Back-up L1 Current", Kind.UPS),
        Frequency("backup_f1", 94, "Back-up L1 Frequency", Kind.UPS),
        Integer("load_mode1", 96, "Load Mode L1"),
        Power4("backup_p1", 98, "Back-up L1 Power", Kind.UPS),
        Voltage("backup_v2", 102, "Back-up L2 Voltage", Kind.UPS),
        Current("backup_i2", 104, "Back-up L2 Current", Kind.UPS),
        Frequency("backup_f2", 106, "Back-up L2 Frequency", Kind.UPS),
        Integer("load_mode2", 108, "Load Mode L2"),
        Power4("backup_p2", 110, "Back-up L2 Power", Kind.UPS),
        Voltage("backup_v3", 114, "Back-up L3 Voltage", Kind.UPS),
        Current("backup_i3", 116, "Back-up L3 Current", Kind.UPS),
        Frequency("backup_f3", 118, "Back-up L3 Frequency", Kind.UPS),
        Integer("load_mode3", 120, "Load Mode L3"),
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
        Integer("ups_load", 146, "Ups Load", "%", Kind.UPS),
        Temp("temperature2", 148, "Inverter Temperature 2", Kind.AC),
        Integer("xx150", 150, "Unknown sensor@150"),
        Temp("temperature", 152, "Inverter Temperature", Kind.AC),
        Integer("xx154", 154, "Unknown sensor@154"),
        Integer("xx156", 156, "Unknown sensor@156"),
        Integer("xx158", 158, "Unknown sensor@158"),
        Voltage("vbattery1", 160, "Battery Voltage", Kind.BAT),  # modbus 35180
        Current("ibattery1", 162, "Battery Current", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Calculated("pbattery1", 0,
                   lambda data, _: round(read_voltage(data, 160) * read_current(data, 162)),
                   "Battery Power", "W", Kind.BAT),
        Integer("battery_mode", 168, "Battery Mode code", "", Kind.BAT),
        Enum2("battery_mode_label", 168, BATTERY_MODES_ET, "Battery Mode", "", Kind.BAT),
        Integer("warning_code", 170, "Warning code"),
        Integer("safety_country", 172, "Safety Country code", "", Kind.AC),
        Enum2("safety_country_label", 172, SAFETY_COUNTRIES_ET, "Safety Country", "", Kind.AC),
        Integer("work_mode", 174, "Work Mode code"),
        Enum2("work_mode_label", 174, WORK_MODES_ET, "Work Mode"),
        Integer("operation_mode", 176, "Operation Mode code"),
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

    # Modbus registers from offset 0x9088 (37000), count 0x0b (11)
    __sensors_battery: Tuple[Sensor, ...] = (
        Integer("battery_bms", 0, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 2, "Battery Index", "", Kind.BAT),
        Integer("battery_status", 4, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 6, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 8, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 10, "Battery Discharge Limit", "A", Kind.BAT),
        # Integer("battery_bms_bytes", 12, "Battery BMS bytes", "", Kind.BAT),
        Integer("battery_soc", 14, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 16, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_warning", 20, "Battery Warning", "", Kind.BAT),
    )

    # Modbus registers from offset 0x8ca0 (36000), count 0x11 (17)
    __sensors2: Tuple[Sensor, ...] = (
        Integer("xxx0", 0, "Unknown sensor2@0"),
        Integer("xxx2", 2, "Unknown sensor2@2"),
        Integer("xxx4", 4, "Unknown sensor2@4"),
        Integer("meter_test_status", 6, "Meter Test Status"),
        Integer("meter_comm_status", 8, "Meter Communication Status"),
        Power("active_power1", 10, "Active Power L1", Kind.AC),  # modbus 36005
        Power("active_power2", 12, "Active Power L2", Kind.AC),
        Power("active_power3", 14, "Active Power L3", Kind.AC),
        # 16 = sum of 10,12 and 14 = active power
        Integer("xxx16", 16, "Unknown sensor2@16"),
        Integer("xxx18", 18, "Unknown sensor2@18"),
        Integer("xxx20", 20, "Unknown sensor2@20"),
        Integer("xxx22", 22, "Unknown sensor2@22"),
        Integer("xxx24", 24, "Unknown sensor2@24"),
        Integer("xxx26", 26, "Unknown sensor2@26"),  # METER_POWER_FACTOR ?
        Frequency("meter_freq", 28, "Meter Frequency", Kind.AC),
        Integer("xxx30", 30, "Unknown sensor2@30"),
        Integer("xxx32", 32, "Unknown sensor2@32"),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __settings: Tuple[Sensor, ...] = (
        Integer("switchColdStart", 45248, "Cold start"),
        Integer("switchShadowscan", 45251, "Shadow scan"),
        Integer("switchBackup", 45252, "Backup enabled"),
        Integer("sensitivityCheck", 45246, "Sensitivity check mode"),

        Integer("batteryCapacity", 45350, "Battery capacity", "", Kind.BAT),
        Integer("batteryNumber", 45351, "Battery count", "", Kind.BAT),
        Voltage("batteryChargeVoltage", 45352, "Battery charge voltage", Kind.BAT),
        Current("batteryChargeCurrent", 45353, "Battery charge current", Kind.BAT),
        Voltage("batteryDischargeVoltage", 45354, "Battery discharge voltage", Kind.BAT),
        Current("batteryDischargeCurrent", 45355, "Battery discharge current", Kind.BAT),
        Integer("batteryDischargeDepth", 45356, "Battery discharge depth", "%", Kind.BAT),
        Integer("batteryOfflineDischargeDepth", 45358, "Battery discharge depth (off-line)", "%", Kind.BAT),

        # TODO convert this to float ??
        Integer("powerFactor", 45482, "Power Factor"),

        Integer("batterySocSwitch", 47500, "Battery SoC Switch"),
        Integer("switchBackflowLimit", 47509, "Back-flow enabled"),
        Integer("backflowLimit", 47510, "Back-flow limit"),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)
        self.serial_number = response[6:22].decode("ascii")
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.dsp1_sw_version = read_unsigned_int(response, 32)
        self.dsp2_sw_version = read_unsigned_int(response, 34)
        self.dsp_spn_version = read_unsigned_int(response, 36)
        self.arm_sw_version = read_unsigned_int(response, 38)
        self.arm_svn_version = read_unsigned_int(response, 40)
        self.software_version = response[42:54].decode("ascii")
        self.arm_version = response[54:66].decode("ascii")

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA1)
        data = self._map_response(raw_data[5:-2], self.__sensors, include_unknown_sensors)
        raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
        data.update(self._map_response(raw_data[5:-2], self.__sensors_battery, include_unknown_sensors))
        if include_unknown_sensors:  # all sensors in RUNNING_DATA2 request are not yet know at the moment
            raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA2)
            data.update(self._map_response(raw_data[5:-2], self.__sensors2, include_unknown_sensors))
        return data

    async def read_settings(self, setting_id: str) -> Any:
        setting = {s.id_: s for s in self.settings()}.get(setting_id)
        raw_data = await self._read_from_socket(ModbusReadCommand(setting.offset, 1, 9))
        with io.BytesIO(raw_data[5:-2]) as buffer:
            return setting.read_value(buffer)

    async def read_settings_data(self) -> Dict[str, Any]:
        data = {}
        for setting in self.settings():
            value = await self.read_settings(setting.id_)
            data[setting.id_] = value
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
        return cls.__settings
