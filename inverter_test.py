"""Simple test script to check inverter UDP protocol communication"""
import asyncio
import logging
import sys

import custom_components.goodwe.goodwe_inverter as inverter

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

# Set the appropriate IP address
IP_ADDRESS = "192.168.0.48"

PORT = 8899
TIMEOUT = 2
RETRIES = 3

inverter = asyncio.run(inverter.discover(IP_ADDRESS, PORT, TIMEOUT, RETRIES))
print(f"Identified inverter\n"
      f"- Model: {inverter.model_name}\n"
      f"- SerialNr: {inverter.serial_number}\n"
      f"- Version: {inverter.software_version}"
      )

response = asyncio.run(inverter.read_runtime_data())

for (sensor, _, _, unit, name, _) in inverter.sensors():
    print(f"{sensor}: \t\t {name} = {response[sensor]} {unit}")

#response = asyncio.run(inverter.read_settings_data())

#for (sensor, _, _, unit, name, _) in inverter.settings():
#    print(f"{sensor}: \t\t {name} = {response[sensor]} {unit}")

# print(asyncio.run(inverter.send_command("F703B798000136C7")))
# Read settings
# print(asyncio.run(inverter.send_command("AA55C07F0109000248")))

# General mode
# print(asyncio.run(inverter.send_command("AA55C07F03590100029B")))
# Off grid mode
# print(asyncio.run(inverter.send_command("AA55C07F03590101029C")))
# Backup mode
# print(asyncio.run(inverter.send_command("AA55C07F03590102029D")))

# Get S/N SolarGo
# print(asyncio.run(inverter.send_command("7F03753100280409")))
# Get Data SolarGo
# print(asyncio.run(inverter.send_command("7F0375940049D5C2")))
