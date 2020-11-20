"""Simple test script to scan inverter present on local network"""
import asyncio
import logging
import sys

import custom_components.goodwe.goodwe_inverter as inverter

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

response = asyncio.run(inverter.search_inverters()).decode("utf-8").split(",")
print(f"Located inverter at IP: {response[0]}, mac: {response[1]}, name: {response[2]}")

inverter = asyncio.run(inverter.discover(response[0], 8899))
print(
    f"Identified inverter model: {inverter.model_name}, serialNr: {inverter.serial_number}"
)
