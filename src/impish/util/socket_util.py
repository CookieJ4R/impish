import os
import socket


def send_data(sock: socket.socket, data_to_send: bytes) -> bool:
    """
    Sends data over a specified socket.
    Will first send the length of the packet in bytes over the socket, so the receiving end knows how many bytes to
    expect for the actual message. The data will be sent immediately afterwards.

    :param socket sock: The socket over which the data will be sent
    :param bytes data_to_send: The data to send in bytes

    :return: True if the data was sent successfully, False otherwise
    """
    try:
        data_length = len(data_to_send).to_bytes(4, "little")
        sock.sendall(data_length)
        sock.sendall(data_to_send)
        return True
    except (OSError, BrokenPipeError):
        return False


def try_unlink(socket_path: str):
    """
    Will try to unlink the socket file, if it already exists.

    :param str socket_path: The path to the socket that should be unlinked/removed
    :raise OSError: If the unlinking fails an OSError is raised.
    """
    if os.path.exists(socket_path):
        os.unlink(socket_path)
