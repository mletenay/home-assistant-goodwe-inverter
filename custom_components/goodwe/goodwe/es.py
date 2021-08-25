from typing import Any, Tuple

from .inverter import Inverter, Sensor
from .inverter import SensorKind as Kind
from .protocol import ProtocolCommand, Aa55ProtocolCommand
from .utils import *


class ES(Inverter):
    """Class representing inverter of ES/EM family"""

    _READ_DEVICE_VERSION_INFO: ProtocolCommand = Aa55ProtocolCommand("010200", "0182")
    _READ_DEVICE_RUNNING_DATA: ProtocolCommand = Aa55ProtocolCommand("010600", "0186")
    _READ_DEVICE_SETTINGS_DATA: ProtocolCommand = Aa55ProtocolCommand("010900", "0189")

    __sensors: Tuple[Sensor, ...] = (
        Sensor("vpv1", 0, read_voltage, "V", "PV1 Voltage", Kind.PV),
        Sensor("ipv1", 2, read_current, "A", "PV1 Current", Kind.PV),
        Sensor("ppv1", 0, lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)), "W", "PV1 Power",
               Kind.PV),
        Sensor("pv1_mode", 4, read_byte, "", "PV1 Mode", Kind.PV),
        Sensor("pv1_mode_label", 4, read_pv_mode1, "", "PV1 Mode", Kind.PV),
        Sensor("vpv2", 5, read_voltage, "V", "PV2 Voltage", Kind.PV),
        Sensor("ipv2", 7, read_current, "A", "PV2 Current", Kind.PV),
        Sensor("ppv2", 0, lambda data, _: round(read_voltage(data, 5) * read_current(data, 7)), "W", "PV2 Power",
               Kind.PV),
        Sensor("pv2_mode", 9, read_byte, "", "PV2 Mode", Kind.PV),
        Sensor("pv2_mode_label", 9, read_pv_mode1, "", "PV2 Mode", Kind.PV),
        Sensor("ppv", 0,
               lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)) + round(
                   read_voltage(data, 5) * read_current(data, 7)),
               "W", "PV Power", Kind.PV),
        Sensor("vbattery1", 10, read_voltage, "V", "Battery Voltage", Kind.BAT),
        # Sensor("vbattery2", 12, read_voltage, "V", "Battery Voltage 2", Kind.BAT),
        # Sensor("vbattery3", 14, read_voltage, "V", "Battery Voltage 3", Kind.BAT),
        Sensor("battery_temperature", 16, read_temp, "C", "Battery Temperature", Kind.BAT),
        Sensor("ibattery1", 18, lambda data, _: abs(read_current(data, 18)) * (-1 if read_byte(data, 30) == 3 else 1),
               "A", "Battery Current", Kind.BAT),
        # round(vbattery1 * ibattery1),
        Sensor("pbattery1", 0,
               lambda data, _: abs(
                   round(read_voltage(data, 10) * read_current(data, 18))
               ) * (-1 if read_byte(data, 30) == 3 else 1),
               "W", "Battery Power", Kind.BAT),
        Sensor("battery_charge_limit", 20, read_bytes2, "A", "Battery Charge Limit", Kind.BAT),
        Sensor("battery_discharge_limit", 22, read_bytes2, "A", "Battery Discharge Limit", Kind.BAT),
        Sensor("battery_status", 24, read_bytes2, "", "Battery Status", Kind.BAT),
        Sensor("battery_soc", 26, read_byte, "%", "Battery State of Charge", Kind.BAT),
        # Sensor("cbattery2", 27, read_byte, "%", "Battery State of Charge 2", Kind.BAT),
        # Sensor("cbattery3", 28, read_byte, "%", "Battery State of Charge 3", Kind.BAT),
        Sensor("battery_soh", 29, read_byte, "%", "Battery State of Health", Kind.BAT),
        Sensor("battery_mode", 30, read_byte, "", "Battery Mode code", Kind.BAT),
        Sensor("battery_mode_label", 30, read_battery_mode1, "", "Battery Mode", Kind.BAT),
        Sensor("battery_warning", 31, read_bytes2, "", "Battery Warning", Kind.BAT),
        Sensor("meter_status", 33, read_byte, "", "Meter Status code", Kind.AC),
        Sensor("vgrid", 34, read_voltage, "V", "On-grid Voltage", Kind.AC),
        Sensor("igrid", 36, read_current, "A", "On-grid Current", Kind.AC),
        Sensor("pgrid", 38,
               lambda data, _: abs(read_power2(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1),
               "W", "On-grid Export Power", Kind.AC),
        Sensor("fgrid", 40, read_freq, "Hz", "On-grid Frequency", Kind.AC),
        Sensor("grid_mode", 42, read_byte, "", "Work Mode code", Kind.AC),
        Sensor("grid_mode_label", 42, read_work_mode1, "", "Work Mode", Kind.AC),
        Sensor("vload", 43, read_voltage, "V", "Back-up Voltage", Kind.UPS),
        Sensor("iload", 45, read_current, "A", "Back-up Current", Kind.UPS),
        Sensor("pload", 47, read_power2, "W", "On-grid Power", Kind.AC),
        Sensor("fload", 49, read_freq, "Hz", "Back-up Frequency", Kind.UPS),
        Sensor("load_mode", 51, read_byte, "", "Load Mode code", Kind.AC),
        Sensor("load_mode_label", 51, read_load_mode1, "", "Load Mode", Kind.AC),
        Sensor("work_mode", 52, read_byte, "", "Energy Mode code", Kind.AC),
        Sensor("work_mode_label", 52, read_energy_mode1, "", "Energy Mode", Kind.AC),
        Sensor("temperature", 53, read_temp, "C", "Inverter Temperature", None),
        Sensor("error_codes", 55, read_bytes4, "", "Error Codes", None),
        Sensor("e_total", 59, read_power_k, "kWh", "Total PV Generation", Kind.PV),
        Sensor("h_total", 63, read_bytes4, "", "Hours Total", Kind.PV),
        Sensor("e_day", 67, read_power_k2, "kWh", "Today's PV Generation", Kind.PV),
        Sensor("e_load_day", 69, read_power_k2, "kWh", "Today's Load", None),
        Sensor("e_load_total", 71, read_power_k, "kWh", "Total Load", None),
        Sensor("total_power", 75, read_power2, "W", "Total Power", None),
        Sensor("effective_work_mode", 77, read_byte, "", "Effective Work Mode code", None),
        # Effective relay control 78-79
        Sensor("grid_in_out", 80, read_byte, "", "On-grid Mode code", Kind.AC),
        Sensor("grid_in_out_label", 0,
               lambda data, _: GRID_MODES.get(read_byte(data, 80)),
               "", "On-grid Mode", Kind.AC),
        Sensor("pback_up", 81, read_power2, "W", "Back-up Power", Kind.UPS),
        # pload + pback_up
        Sensor("plant_power", 0,
               lambda data, _: round(read_power2(data, 47) + read_power2(data, 81)),
               "W", "Plant Power", Kind.AC),
        Sensor("diagnose_result", 89, read_bytes4, "", "Diag Status", None),
        # ppv1 + ppv2 + pbattery - pgrid
        Sensor("house_consumption", 0,
               lambda data, _: round(read_voltage(data, 0) * read_current(data, 2)) + round(
                   read_voltage(data, 5) * read_current(data, 7)) + (
                                       abs(round(read_voltage(data, 10) * read_current(data, 18)))
                                       * (-1 if read_byte(data, 30) == 3 else 1)
                               ) - (abs(read_power2(data, 38)) * (-1 if read_byte(data, 80) == 2 else 1)),
               "W", "House Comsumption", Kind.AC),
    )

    __settings: Tuple[Sensor, ...] = (
        Sensor("charge_power_limit", 4, read_bytes2, "", "Charge Power Limit Value", None),
        Sensor("discharge_power_limit", 10, read_bytes2, "", "Disharge Power Limit Value", None),
        Sensor("relay_control", 13, read_byte, "", "Relay Control", None),
        Sensor("off-grid_charge", 15, read_byte, "", "Off-grid Charge", None),
        Sensor("shadow_scan", 17, read_byte, "", "Shadow Scan", None),
        Sensor("backflow_state", 18, read_bytes2, "", "Backflow State", None),
        Sensor("capacity", 22, read_bytes2, "", "Capacity", None),
        Sensor("charge_v", 24, read_bytes2, "V", "Charge Voltage", None),
        Sensor("charge_i", 26, read_bytes2, "A", "Charge Current", None),
        Sensor("discharge_i", 28, read_bytes2, "A", "Discharge Current", None),
        Sensor("discharge_v", 30, read_bytes2, "V", "Discharge Voltage", None),
        Sensor("dod", 32, lambda data, _: 100 - read_bytes2(data, 32), "%", "Depth of Discharge", None),
        Sensor("battery_activated", 34, read_bytes2, "", "Battery Activated", None),
        Sensor("bp_off_grid_charge", 36, read_bytes2, "", "BP Off-grid Charge", None),
        Sensor("bp_pv_discharge", 38, read_bytes2, "", "BP PV Discharge", None),
        Sensor("bp_bms_protocol", 40, read_bytes2, "", "BP BMS Protocol", None),
        Sensor("power_factor", 42, read_bytes2, "", "Power Factor", None),
        Sensor("grid_up_limit", 52, read_bytes2, "", "Grid Up Limit", None),
        Sensor("soc_protect", 56, read_bytes2, "", "SoC Protect", None),
        Sensor("work_mode", 66, read_bytes2, "", "Work Mode", None),
        Sensor("grid_quality_check", 68, read_bytes2, "", "Grid Quality Check", None),
    )

    async def read_device_info(self):
        response = await self._read_from_socket(self._READ_DEVICE_VERSION_INFO)
        self.model_name = response[12:22].decode("ascii").rstrip()
        self.serial_number = response[38:54].decode("ascii")
        self.software_version = response[58:70].decode("ascii")

    async def read_runtime_data(self, include_unknown_sensors: bool = False) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_RUNNING_DATA)
        data = self._map_response(raw_data[7:-2], self.__sensors, include_unknown_sensors)
        return data

    async def read_settings_data(self) -> Dict[str, Any]:
        raw_data = await self._read_from_socket(self._READ_DEVICE_SETTINGS_DATA)
        data = self._map_response(raw_data[7:-2], self.__settings)
        return data

    async def set_work_mode(self, work_mode: int):
        if work_mode in (0, 1, 2):
            await self._read_from_socket(
                Aa55ProtocolCommand("035901" + "{:02x}".format(work_mode), "03D9")
            )

    async def set_ongrid_battery_dod(self, dod: int):
        if 0 <= dod <= 89:
            await self._read_from_socket(
                Aa55ProtocolCommand("023905056001" + "{:04x}".format(100 - dod), "02b9")
            )

    @classmethod
    def sensors(cls) -> Tuple[Sensor, ...]:
        return cls.__sensors

    @classmethod
    def settings(cls) -> Tuple[Sensor, ...]:
        return cls.__settings
