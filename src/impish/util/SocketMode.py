from enum import Enum, auto


class SocketMode(Enum):
    """
    This enum represents the different socket modes.
    """
    UNIX_DOMAIN_SOCKET = auto()
    INET_SOCKET = auto()
