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
response = asyncio.run(inverter.read_runtime_data())

for (sensor, _, _, unit, name, _) in inverter.sensors():
    print(f"{sensor}: \t\t {name} = {response[sensor]} {unit}")


# print(asyncio.run(inverter.send_command("AA55C07F0102000241", (80,))))

# print(asyncio.run(inverter.send_command("F703B798000136C7")))
# Read settings
# print(asyncio.run(inverter.send_command("AA55C07F0109000248")))

# General mode
# print(asyncio.run(inverter.send_command("AA55C07F03590100029B")))
# Off grid mode
# print(asyncio.run(inverter.send_command("AA55C07F03590101029C")))
# Backup mode
# print(asyncio.run(inverter.send_command("AA55C07F03590102029D")))
# b"\xaaU\x7f\xc0\x01\x82L0303<GW10K-ET  \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009010KETU204W0357\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 02041-12-S0<\x0c\xb1"

# Get S/N SolarGo
# print(asyncio.run(inverter.send_command("7F03753100280409")))
# Get Data SolarGo
# print(asyncio.run(inverter.send_command("7F0375940049D5C2")))

data = bytes.fromhex(
    "aa55f703fa140a0d172331000000000000000000000000000000000000000000000000000000000000000000000000093d000613890000000c0953000613880000000c094a000613880000000f00010000001a0000fc500000000000000000093b000b13890001000000e8094c00021388000100000006094b0002138800010000001a000000fd0000003f0000019200000107000002c3000301440000011400001e320f1909aa00000000000600010000002000010000000000000000289f00000017000000ab000006e30004000000160015000026e300bb0000130f00290000109c000000050000000100000000000000000001030800200002000000000a25"
)
data = data[5:-2]
print(int.from_bytes(data[156:157], byteorder="big", signed=True))
print(int.from_bytes(data[157:158], byteorder="big", signed=True))
print(int.from_bytes(data[158:159], byteorder="big", signed=True))
print(int.from_bytes(data[159:160], byteorder="big", signed=True))
print(int.from_bytes(data[156:158], byteorder="big", signed=True))
print(int.from_bytes(data[158:160], byteorder="big", signed=True))
print(int.from_bytes(data[156:160], byteorder="big", signed=True))
print(int.from_bytes(data[42:44], byteorder="big", signed=True))
print(data[80] * 256 + data[81])
