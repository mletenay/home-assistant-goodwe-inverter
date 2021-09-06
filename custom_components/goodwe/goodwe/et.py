from typing import Tuple

from .inverter import Inverter
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, ModbusReadCommand, ModbusWriteCommand
from .sensor import *


class ET(Inverter):
    """Class representing inverter of ET family"""

    # Modbus registers from offset 0x891c (35100), count 0x7d (125)
    __all_sensors: Tuple[Sensor, ...] = (
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
        # Byte("pv4_mode", 38, "PV4 Mode", "", Kind.PV),
        # Byte("pv3_mode", 39, "PV3 Mode", "", Kind.PV),
        Byte("pv2_mode", 40, "PV2 Mode code", "", Kind.PV),
        Enum("pv2_mode_label", 40, PV_MODES, "PV2 Mode", "", Kind.PV),
        Byte("pv1_mode", 41, "PV1 Mode code", "", Kind.PV),
        Enum("pv1_mode_label", 41, PV_MODES, "PV1 Mode", "", Kind.PV),
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
        Integer("grid_mode", 72, "Grid Mode code", "", Kind.PV),
        Enum2("grid_mode_label", 72, GRID_MODES, "Grid Mode", "", Kind.PV),
        Power4("total_inverter_power", 74, "Total Power", Kind.AC),
        Power4("active_power", 78, "Active Power", Kind.GRID),
        Calculated("grid_in_out", 78, lambda data, _: read_grid_mode(data, 78), "On-grid Mode code", "", Kind.GRID),
        Calculated("grid_in_out_label", 0, lambda data, _: GRID_IN_OUT_MODES.get(read_grid_mode(data, 78)),
                   "On-grid Mode",
                   "", Kind.GRID),
        Power4("reactive_power", 82, "Reactive Power", Kind.GRID),
        Power4("apparent_power", 86, "Apparent Power", Kind.GRID),
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
        Temp("temperature_air", 148, "Inverter Temperature (Air))", Kind.AC),
        Temp("temperature_module", 150, "Inverter Temperature (Module)"),
        Temp("temperature", 152, "Inverter Temperature (Radiator)", Kind.AC),
        Integer("xx154", 154, "Unknown sensor@154"),
        Voltage("bus_voltage", 156, "Bus Voltage", None),
        Voltage("nbus_voltage", 158, "NBus Voltage", None),
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
        Calculated("errors", 0,
                   lambda data, _: decode_bitmap(read_bytes4(data, 178), ERROR_CODES),
                   "Errors", ""),
        Energy4("e_total", 182, "Total PV Generation", Kind.PV),
        Energy4("e_day", 186, "Today's PV Generation", Kind.PV),
        Energy4("e_total_exp", 190, "Total Energy (export)", Kind.AC),
        Long("h_total", 194, "Hours Total", "h", Kind.PV),
        Energy("e_day_exp", 198, "Today Energy (export)", Kind.AC),
        Energy4("e_total_imp", 200, "Total Energy (import)", Kind.AC),
        Energy("e_day_imp", 204, "Today Energy (import)", Kind.AC),
        Energy4("e_load_total", 206, "Total Load", Kind.AC),
        Energy("e_load_day", 210, "Today Load", Kind.AC),
        Energy4("e_bat_charge_total", 212, "Total Battery Charge", Kind.BAT),
        Energy("e_bat_charge_day", 216, "Today Battery Charge", Kind.BAT),
        Energy4("e_bat_discharge_total", 218, "Total Battery Discharge", Kind.BAT),
        Energy("e_bat_discharge_day", 222, "Today Battery Discharge", Kind.BAT),
        Long("diagnose_result", 240, "Diag Status"),
        # ppv1 + ppv2 + pbattery - active_power
        Calculated("house_consumption", 0,
                   lambda data, _: read_power(data, 10) + read_power(data, 18) + round(
                       read_voltage(data, 160) * read_current(data, 162)) - read_power(data, 78),
                   "House Comsumption", "W", Kind.AC),
    )

    # Modbus registers from offset 0x9088 (37000)
    __all_sensors_battery: Tuple[Sensor, ...] = (
        Integer("battery_bms", 0, "Battery BMS", "", Kind.BAT),
        Integer("battery_index", 2, "Battery Index", "", Kind.BAT),
        Integer("battery_status", 4, "Battery Status", "", Kind.BAT),
        Temp("battery_temperature", 6, "Battery Temperature", Kind.BAT),
        Integer("battery_charge_limit", 8, "Battery Charge Limit", "A", Kind.BAT),
        Integer("battery_discharge_limit", 10, "Battery Discharge Limit", "A", Kind.BAT),
        Integer("battery_error_l", 12, "Battery Error L", "", Kind.BAT),
        Integer("battery_soc", 14, "Battery State of Charge", "%", Kind.BAT),
        Integer("battery_soh", 16, "Battery State of Health", "%", Kind.BAT),
        Integer("battery_modules", 18, "Battery Modules", "", Kind.BAT),  # modbus 37009
        Integer("battery_warning_l", 20, "Battery Warning L", "", Kind.BAT),
        Integer("battery_protocol", 22, "Battery Protocol", "", Kind.BAT),
        Integer("battery_error_h", 24, "Battery Error H", "", Kind.BAT),
        Calculated("battery_error", 0,
                   lambda data, _: decode_bitmap(read_bytes2(data, 24) << 16 + read_bytes2(data, 12), BMS_ALARM_CODES),
                   "Battery Error", "", Kind.BAT),
        Integer("battery_warning_h", 28, "Battery Warning H", "", Kind.BAT),
        Calculated("battery_warning", 0,
                   lambda data, _: decode_bitmap(read_bytes2(data, 28) << 16 + read_bytes2(data, 20),
                                                 BMS_WARNING_CODES),
                   "Battery Error", "", Kind.BAT),
        Integer("battery_sw_version", 30, "Battery Software Version", "", Kind.BAT),
        Integer("battery_hw_version", 32, "Battery Hardware Version", "", Kind.BAT),
        Integer("battery_max_cell_temp_id", 34, "Battery Max Cell Temperature ID", "", Kind.BAT),
        Integer("battery_min_cell_temp_id", 36, "Battery Min Cell Temperature ID", "", Kind.BAT),
        Integer("battery_max_cell_voltage_id", 38, "Battery Max Cell Voltage ID", "", Kind.BAT),
        Integer("battery_min_cell_voltage_id", 40, "Battery Min Cell Voltage ID", "", Kind.BAT),
        Temp("battery_max_cell_temp", 42, "Battery Max Cell Temperature", Kind.BAT),
        Temp("battery_min_cell_temp", 44, "Battery Min Cell Temperature", Kind.BAT),
        Voltage("battery_max_cell_voltage", 46, "Battery Max Cell Voltage", Kind.BAT),
        Voltage("battery_min_cell_voltage", 48, "Battery Min Cell Voltage", Kind.BAT),
    )

    # Inverter's meter data
    # Modbus registers from offset 0x8ca0 (36000)
    __all_sensors_meter: Tuple[Sensor, ...] = (
        Integer("commode", 0, "Commode"),
        Integer("rssi", 2, "RSSI"),
        Integer("manufacture_code", 4, "Manufacture Code"),
        Integer("meter_test_status", 6, "Meter Test Status"),  # 1: correct，2: reverse，3: incorrect，0: not checked
        Integer("meter_comm_status", 8, "Meter Communication Status"),  # 1 OK, 0 NotOK
        Power("active_power1", 10, "Active Power L1", Kind.GRID),  # modbus 36005
        Power("active_power2", 12, "Active Power L2", Kind.GRID),
        Power("active_power3", 14, "Active Power L3", Kind.GRID),
        Integer("active_power_total", 16, "Active Power Total", "W", Kind.GRID),
        Integer("reactive_power_total", 18, "Reactive Power Total", "W", Kind.GRID),
        Decimal("meter_power_factor1", 20, 100, "Meter Power Factor L1", "", Kind.GRID),
        Decimal("meter_power_factor2", 22, 100, "Meter Power Factor L2", "", Kind.GRID),
        Decimal("meter_power_factor3", 24, 100, "Meter Power Factor L3", "", Kind.GRID),
        Decimal("meter_power_factor", 26, 100, "Meter Power Factor", "", Kind.GRID),
        Frequency("meter_freq", 28, "Meter Frequency", Kind.GRID),  # modbus 36014
        Float("meter_e_total_exp", 30, 1000, "Meter Total Energy (export)", "kWh", Kind.GRID),
        Float("meter_e_total_imp", 34, 1000, "Meter Total Energy (import)", "kWh", Kind.GRID),
        Long("meter_active_power1", 38, "Meter Active Power L1", "W", Kind.GRID),
        Long("meter_active_power2", 42, "Meter Active Power L2", "W", Kind.GRID),
        Long("meter_active_power3", 46, "Meter Active Power L3", "W", Kind.GRID),
        Long("meter_active_power_total", 50, "Meter Active Power Total", "W", Kind.GRID),
        Long("meter_reactive_power1", 54, "Meter Reactive Power L1", "W", Kind.GRID),
        Long("meter_reactive_power2", 58, "Meter Reactive Power L2", "W", Kind.GRID),
        Long("meter_reactive_power3", 62, "Meter Reactive Power L2", "W", Kind.GRID),
        Long("meter_reactive_power_total", 66, "Meter Reactive Power Total", "W", Kind.GRID),
        Long("meter_apparent_power1", 70, "Meter Apparent Power L1", "", Kind.GRID),
        Long("meter_apparent_power2", 74, "Meter Apparent Power L2", "", Kind.GRID),
        Long("meter_apparent_power3", 78, "Meter Apparent Power L3", "", Kind.GRID),
        Long("meter_apparent_power_total", 82, "Meter Apparent Power Total", "", Kind.GRID),
        Integer("meter_type", 86, "Meter Type", "", Kind.GRID),
        Integer("meter_sw_version", 88, "Meter Software Version", "", Kind.GRID),
    )

    # Modbus registers of inverter settings, offsets are modbus register addresses
    __all_settings: Tuple[Sensor, ...] = (
        Integer("cold_start", 45248, "Cold Start", "", Kind.AC),
        Integer("shadow_scan", 45251, "Shadow Scan", "", Kind.PV),
        Integer("backup_supply", 45252, "Backup Supply", "", Kind.UPS),
        Integer("sensitivity_check", 45246, "Sensitivity Check Mode", "", Kind.AC),

        Integer("battery_capacity", 45350, "Battery Capacity", "Ah", Kind.BAT),
        Integer("battery_modules", 45351, "Battery Modules", "", Kind.BAT),
        Voltage("battery_charge_voltage", 45352, "Battery Charge Voltage", Kind.BAT),
        Current("battery_charge_current", 45353, "Battery Charge Current", Kind.BAT),
        Voltage("battery_discharge_voltage", 45354, "Battery Discharge Voltage", Kind.BAT),
        Current("battery_discharge_current", 45355, "Battery Discharge Current", Kind.BAT),
        Integer("battery_discharge_depth", 45356, "Battery Discharge Depth", "%", Kind.BAT),
        Voltage("battery_discharge_voltage_offline", 45357, "Battery Discharge Voltage (off-line)", Kind.BAT),
        Integer("battery_discharge_depth_offline", 45358, "Battery Discharge Depth (off-line)", "%", Kind.BAT),

        Decimal("power_factor", 45482, 100, "Power Factor"),

        Integer("work_mode", 47000, "Work Mode", "", Kind.AC),

        Integer("battery_soc_protection", 47500, "Battery SoC Protection", "", Kind.BAT),

        Integer("grid_export", 47509, "Grid Export Enabled", "", Kind.GRID),
        Integer("grid_export_limit", 47510, "Grid Export Limit", "W", Kind.GRID),
    )

    def __init__(self, host: str, comm_addr: int = 0, timeout: int = 1, retries: int = 3):
        super().__init__(host, comm_addr, timeout, retries)
        if not self.comm_addr:
            # Set the default inverter address
            self.comm_addr = 0xf7
        self._READ_DEVICE_VERSION_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x88b8, 0x0021)
        self._READ_RUNNING_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x891c, 0x007d)
        self._READ_METER_DATA: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x8ca0, 0x2d)
        self._READ_BATTERY_INFO: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0x9088, 0x0018)
        self._GET_WORK_MODE: ProtocolCommand = ModbusReadCommand(self.comm_addr, 0xb798, 0x0001)
        self._has_battery: bool = True
        self._is_single_phase: bool = False
        self._sensors = self.__all_sensors
        self._sensors_battery = self.__all_sensors_battery
        self._sensors_meter = self.__all_sensors_meter
        self._settings = self.__all_settings

    @staticmethod
    def _is_not_3phase_sensor(s: Sensor) -> bool:
        return not ((s.id_.endswith('2') or s.id_.endswith('3')) and 'pv' not in s.id_)

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        response = response[5:-2]
        # Modbus registers from offset (35000)
        self.modbus_version = read_unsigned_int(response, 0)
        self.rated_power = read_unsigned_int(response, 2)
        self.ac_output_type = read_unsigned_int(response, 4)  # 0: 1-phase, 1: 3-phase (4 wire), 2: 3-phase (3 wire)
        self.serial_number = response[6:22].decode("ascii")
        self.model_name = response[22:32].decode("ascii").rstrip()
        self.dsp1_sw_version = read_unsigned_int(response, 32)
        self.dsp2_sw_version = read_unsigned_int(response, 34)
        self.dsp_spn_version = read_unsigned_int(response, 36)
        self.arm_sw_version = read_unsigned_int(response, 38)
        self.arm_svn_version = read_unsigned_int(response, 40)
        self.software_version = response[42:54].decode("ascii")
        self.arm_version = response[54:66].decode("ascii")

        if "EHU" in self.serial_number:
            self._is_single_phase = True
            # this is single phase inverter, filter out all L2 and L3 sensors
            self._sensors = tuple(filter(self._is_not_3phase_sensor, self.__all_sensors))

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_RUNNING_DATA)
        data = self._map_response(raw_data[5:-2], self._sensors, include_unknown_sensors)

        self._has_battery = data.get('battery_mode', 0) != 0
        if self._has_battery:
            raw_data = await self._read_from_socket(self._READ_BATTERY_INFO)
            data.update(self._map_response(raw_data[5:-2], self._sensors_battery, include_unknown_sensors))

        raw_data = await self._read_from_socket(self._READ_METER_DATA)
        data.update(self._map_response(raw_data[5:-2], self._sensors_meter, include_unknown_sensors))
        return data

    async def read_settings(self, setting_id: str) -> Any:
        setting: Sensor = {s.id_: s for s in self.settings()}.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        raw_data = await self._read_from_socket(ModbusReadCommand(self.comm_addr, setting.offset, 1))
        with io.BytesIO(raw_data[5:-2]) as buffer:
            return setting.read_value(buffer)

    async def write_settings(self, setting_id: str, value: Any):
        setting: Sensor = {s.id_: s for s in self.settings()}.get(setting_id)
        if not setting:
            raise ValueError(f'Unknown setting "{setting_id}"')
        raw_value = setting.encode_value(value)
        if len(raw_value) > 2:
            raise NotImplementedError()
        value = int.from_bytes(raw_value, byteorder="big", signed=True)
        await self._read_from_socket(ModbusWriteCommand(self.comm_addr, setting.offset, value))

    async def read_settings_data(self) -> Dict[str, Any]:
        data = {}
        for setting in self.settings():
            value = await self.read_settings(setting.id_)
            data[setting.id_] = value
        return data

    async def set_grid_export_limit(self, export_limit: int):
        if export_limit >= 0 or export_limit <= 10000:
            return await self.write_settings('grid_export_limit', export_limit)

    async def set_work_mode(self, work_mode: int):
        if work_mode in (0, 1, 2):
            return await self.write_settings('work_mode', work_mode)

    async def set_ongrid_battery_dod(self, dod: int):
        if 0 <= dod <= 89:
            return await self.write_settings('battery_discharge_depth', 100 - dod)

    def sensors(self) -> Tuple[Sensor, ...]:
        if self._has_battery:
            return self._sensors + self._sensors_battery + self._sensors_meter
        else:
            return self._sensors + self._sensors_meter

    def settings(self) -> Tuple[Sensor, ...]:
        return self._settings
