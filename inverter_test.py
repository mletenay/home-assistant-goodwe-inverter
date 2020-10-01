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
IP_ADDRESS = "192.168.1.14"

inverter = asyncio.run(inverter.discover(IP_ADDRESS, 8899))
response = asyncio.run(inverter.get_data())

for (sensor, _, _, unit, name, _) in inverter.sensors():
    print(f"{sensor}: {name} = {response[sensor]} {unit}")

# print(asyncio.run(inverter.send_command("f70388b800213ac1")))
