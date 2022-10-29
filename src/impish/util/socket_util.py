import socket


def send_data(sock: socket.socket, data_to_send: bytes) -> bool:
    try:
        data_length = len(data_to_send).to_bytes(4, "little")
        sock.sendall(data_length)
        sock.sendall(data_to_send)
        return True
    except (OSError, BrokenPipeError):
        return False
