from enum import auto, IntEnum


class MessageType(IntEnum):
    """
    This enum represents the different message types.
    """
    SUBSCRIBE_MESSAGE = auto()
    DATA_MESSAGE = auto()
