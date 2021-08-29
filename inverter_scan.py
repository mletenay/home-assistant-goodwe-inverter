"""Simple test script to scan inverter present on local network"""
import asyncio
import logging
import sys
import binascii

import custom_components.goodwe.goodwe.goodwe as inverter
from custom_components.goodwe.goodwe.protocol import ProtocolCommand

logging.basicConfig(
    format="%(asctime)-15s %(funcName)s(%(lineno)d) - %(levelname)s: %(message)s",
    stream=sys.stderr,
    level=getattr(logging, "DEBUG", None),
)

def try_command(command, ip):
    print(f"Trying command: {command}")
    try:
        response = asyncio.run(ProtocolCommand(bytes.fromhex(command), lambda x: True).execute(result[0], 8899))
        print(f"Response to {command} command: {response.hex()}")
    except Exception as err:
        print(f"No response to {command} command")


def omnik_command(logger_sn):
    #frame = (headCode) + (dataFieldLength) + (contrlCode) + (sn) + (sn) + (command) + (checksum) + (endCode)
    frame_hdr = binascii.unhexlify('680241b1') #from SolarMan / new Omnik app
    command = binascii.unhexlify('0100')
    defchk = binascii.unhexlify('87')
    endCode = binascii.unhexlify('16')

    #tar = bytearray.fromhex(hex(logger_sn)[8:10] + hex(logger_sn)[6:8] + hex(logger_sn)[4:6] + hex(logger_sn)[2:4])
    #frame = bytearray(frame_hdr + tar + tar + command + defchk + endCode)
    frame = bytearray(frame_hdr + binascii.unhexlify(logger_sn) + command + defchk + endCode)

    checksum = 0
    frame_bytes = bytearray(frame)
    for i in range(1, len(frame_bytes) - 2, 1):
        checksum += frame_bytes[i] & 255
    frame_bytes[len(frame_bytes) - 2] = int((checksum & 255))
    return frame_bytes.hex()

result = asyncio.run(inverter.search_inverters()).decode("utf-8").split(",")
print(f"Located inverter at IP: {result[0]}, mac: {result[1]}, name: {result[2]}")


# EM/ES
try_command("AA55C07F0102000241", result[0])
# DT (SolarGo)
try_command("7F03753100280409", result[0])
# Omnik v5 ?
try_command("197d0001000dff045e50303036564657f6e60d", result[0])
# Omnik 4 ?
sn = bytes(result[2][10:], 'utf-8').hex()
try_command(omnik_command(sn), result[0])
# Omnik 4 reversed ?
sn = "".join(reversed([sn[i:i+2] for i in range(0, len(sn), 2)]))
try_command(omnik_command(sn), result[0])


print(f"Identifying inverter at IP: {result[0]}")
inverter = asyncio.run(inverter.discover(result[0], 8899))
print(
    f"Identified inverter model: {inverter.model_name}, serialNr: {inverter.serial_number}"
)
