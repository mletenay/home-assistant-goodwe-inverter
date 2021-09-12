"""Simple test script to check inverter UDP protocol communication"""
import asyncio
import goodwe
import logging
import sys


logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

# Set the appropriate IP address
IP_ADDRESS = "192.168.1.14"

FAMILY = "ET"  # One of ET, EH, ES, EM, DT, NS, XS, BP or None to detect inverter family automatically
COMM_ADDR = None  # Usually 0xf7 for ET/EH or 0x7f for DT/D-NS/XS, or None for default value
TIMEOUT = 1
RETRIES = 3

inverter = asyncio.run(goodwe.connect(IP_ADDRESS, COMM_ADDR, FAMILY, TIMEOUT, RETRIES))
print(
    f"Identified inverter\n"
    f"- Model: {inverter.model_name}\n"
    f"- SerialNr: {inverter.serial_number}\n"
    f"- Version: {inverter.software_version}"
)

response = asyncio.run(inverter.read_runtime_data())

for sensor in inverter.sensors():
    if sensor.id_ in response:
        print(f"{sensor.id_}: \t\t {sensor.name} = {response[sensor.id_]} {sensor.unit}")

# response = asyncio.run(inverter.read_settings_data())

# for setting in inverter.settings():
#    print(f"{setting.id_}: \t\t {setting.name} = {response[setting.id_]} {setting.unit}")

# response = asyncio.run(goodwe.protocol.ModbusReadCommand(0xf7, 0x88b8, 1).execute(IP_ADDRESS, TIMEOUT, RETRIES))
# print(response.hex())
