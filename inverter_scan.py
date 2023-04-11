"""Simple test script to scan inverter present on local network"""
import asyncio
import goodwe
import logging
import sys

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "ERROR", None),
)

result = asyncio.run(goodwe.search_inverters()).decode("utf-8").split(",")
print(f"Located inverter at IP: {result[0]}, mac: {result[1]}, name: {result[2]}")

inverter = asyncio.run(goodwe.discover(result[0], 8899))
print(
    f"Identified inverter model: {inverter.model_name}, serialNr: {inverter.serial_number}"
)
