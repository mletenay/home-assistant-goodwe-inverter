import asyncio
import logging
from typing import Tuple

from .dt import DT
from .eh import EH
from .es import ES
from .et import ET
from .exceptions import InverterError, ProcessingException
from .inverter import Inverter, Sensor, SensorKind
from .protocol import UdpInverterProtocol, Aa55ProtocolCommand

logger = logging.getLogger(__name__)

# registry of supported inverter protocols
# TODO: it breaks when EH is not first with EH inverter during discovery
_SUPPORTED_PROTOCOLS = [EH, ET, DT, ES]


async def connect(host: str, port: int = 8899, family: str = None, timeout: int = 2, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified host/port and answer appropriate Inverter instance.
    To improve performance, it is recommended to provide the inverter family name,
    however it it is not explicitly provided, the code will try do detect the family automatically.

    Supported inverter family names are ET, EH, ES, EM, DT, NS, XS, BP

    Raise InverterError if unable to contact or recognise supported inverter
    """
    if "ET" == family:
        inverter = ET(host, port, timeout, retries)
    elif "EH" == family:
        inverter = EH(host, port, timeout, retries)
    elif "ES" == family or "EM" == family or "BP" == family:
        inverter = ES(host, port, timeout, retries)
    elif "DT" == family or "NS" == family or "XS" == family:
        inverter = DT(host, port, timeout, retries)
    else:
        return await discover(host, port, timeout, retries)

    logger.debug(f"Connecting to {family} family inverter at {host}:{port}")
    await inverter.read_device_info()
    logger.debug(f"Connected to inverter {inverter.model_name}, S/N:{inverter.serial_number}")
    return inverter


async def search_inverters() -> bytes:
    """Scan the network for inverters

    Raise InverterError if unable to contact any inverter
    """
    logger.debug("Searching inverters by broadcast to port 48899")
    loop = asyncio.get_running_loop()
    on_response_received = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: UdpInverterProtocol(
            "WIFIKIT-214028-READ".encode("utf-8"),
            lambda r: True,
            on_response_received,
        ),
        remote_addr=("255.255.255.255", 48899),
        allow_broadcast=True,
    )
    try:
        await on_response_received
        result = on_response_received.result()
        if result is not None:
            return result
        else:
            raise InverterError("No response received to broadcast request")
    except asyncio.CancelledError:
        raise InverterError("No valid response received to broadcast request") from None
    finally:
        transport.close()


async def discover(host: str, port: int = 8899, timeout: int = 2, retries: int = 3) -> Inverter:
    """Contact the inverter at the specified value and answer appropriate Inverter instance

    Raise InverterError if unable to contact or recognise supported inverter
    """
    failures = []

    # Try the common AA55C07F0102000241 command first and detect inverter type from serial_number
    try:
        logger.debug(f"Probing inverter at {host}:{port}")
        response = await Aa55ProtocolCommand("010200", "0182").execute(host, port, timeout, retries)
        model_name = response[12:22].decode("ascii").rstrip()
        serial_number = response[38:54].decode("ascii")
        if "ETU" in serial_number:
            software_version = response[71:83].decode("ascii").strip()
            logger.debug(f"Detected ET inverter {model_name}, S/N:{serial_number}")
            return ET(host, port, timeout, retries, model_name, serial_number, software_version)
        elif "ESU" in serial_number or "EMU" in serial_number or "BPU" in serial_number or "BPS" in serial_number:
            software_version = response[58:70].decode("ascii").strip()
            # arm_version = response[71:83].decode("ascii").strip()
            logger.debug(f"Detected ES inverter {model_name}, S/N:{serial_number}")
            return ES(host, port, timeout, retries, model_name, serial_number, software_version)
        elif "EHU" in serial_number:  # TODO: check if version is correct
            software_version = response[54:66].decode("ascii")
            logger.debug(f"Detected EH inverter {model_name}, S/N:{serial_number}")
            return EH(host, port, timeout, retries, model_name, serial_number, software_version)
    except InverterError as ex:
        failures.append(ex)

    # Probe inverter specific protocols
    for inverter in _SUPPORTED_PROTOCOLS:
        i = inverter(host, port, timeout, retries)
        try:
            logger.debug(f"Probing {inverter.__name__} inverter at {host}:{port}")
            await i.read_device_info()
            logger.debug(f"Detected {inverter.__name__} protocol inverter {i.model_name}, S/N:{i.serial_number}")
            return i
        except InverterError as ex:
            failures.append(ex)
    raise InverterError(
        "Unable to connect to the inverter at "
        f"host={host} port={port}, or your inverter is not supported yet.\n"
        f"Failures={str(failures)}"
    )
