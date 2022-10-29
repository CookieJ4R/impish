from enum import Enum, auto


class SocketMode(Enum):
    UNIX_DOMAIN_SOCKET = auto()
    INET_SOCKET = auto()
