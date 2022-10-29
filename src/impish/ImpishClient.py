import json
import socket
import threading

from impish.util import socket_util
from impish.util.MessageType import MessageType
from impish.util.SocketMode import SocketMode


class ImpishClient:

    _sock: socket.socket
    _callback_map = {}

    def __init__(self, addr: str, port: int = 5050, mode: SocketMode = SocketMode.UNIX_DOMAIN_SOCKET):
        self._sock_addr = addr
        self._sock_port = port
        self._sock_mode = mode

    def start(self):
        if self._sock_mode == SocketMode.UNIX_DOMAIN_SOCKET:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                self._sock.connect(self._sock_addr)
            except socket.error:
                return
        elif self._sock_mode == SocketMode.INET_SOCKET:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self._sock.connect((self._sock_addr, self._sock_port))
            except socket.error:
                return
        read_thread = threading.Thread(target=self._read_thread, daemon=True)
        read_thread.start()

    def send_data(self, channel: str, message: str, exclude_self: bool = True):
        data = {'msg_type': MessageType.DATA_MESSAGE, 'channel': channel, 'message': message,
                'exclude_self': exclude_self}
        data_to_send = json.dumps(data).encode('utf-8')
        socket_util.send_data(self._sock, data_to_send)

    def subscribe(self, channel: str, callback):
        channel_subscribe_data = {'msg_type': MessageType.SUBSCRIBE_MESSAGE, 'channel': channel}
        data_to_send = json.dumps(channel_subscribe_data).encode('utf-8')
        socket_util.send_data(self._sock, data_to_send)
        self._register_message_received_callback(channel, callback)

    def _register_message_received_callback(self, channel: str, callback):
        if channel in self._callback_map:
            self._callback_map[channel].append(callback)
        else:
            self._callback_map[channel] = [callback]

    def _on_message_received(self, msg):
        decoded_data = json.loads(msg)
        channel = decoded_data['channel']
        if channel in self._callback_map:
            for callback in self._callback_map[channel]:
                callback(decoded_data)

    def _read_thread(self):
        try:
            while True:
                data_length = self._sock.recv(4)
                if not data_length:
                    break
                data_length = int.from_bytes(data_length, byteorder="little")
                data = self._sock.recv(data_length)
                if not data:
                    break
                self._on_message_received(data)
        finally:
            self._sock.close()
