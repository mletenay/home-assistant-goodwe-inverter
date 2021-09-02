class InverterError(Exception):
    """Indicates error communicating with inverter"""


class RequestFailedException(InverterError):
    """Indicates requesting inverter data was unsuccessful"""


class ProcessingException(InverterError):
    """Indicates an error occurred during processing of inverter data"""


class MaxRetriesException(InverterError):
    """Indicates the maximum number of retries has been reached"""


