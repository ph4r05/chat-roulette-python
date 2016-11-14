__author__ = 'dusanklinec'


class Error(Exception):
    """Generic EB client error."""


class InvalidResponse(Error):
    """Invalid server response"""


class InvalidStatus(Error):
    """Invalid server response"""


class RequestFailed(Error):
    """API request failed"""


class EnvError(Error):
    """Problem with the environment running the script"""


class NoSuchEndpoint(Error):
    """Endpoint could not be loaded from the configuration"""


class SubprocessError(Error):
    """Error when executing a subprocess"""

