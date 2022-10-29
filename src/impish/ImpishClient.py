import json
import socket
import threading
from typing import Callable

from impish.util import socket_util
from impish.util.MessageType import MessageType
from impish.util.SocketMode import SocketMode


class ImpishClient:
    """
    The ImpishClient is responsible for publishing messages to the broker, receiving messages on channels
    and registering callbacks for them.
    """

    _sock: socket.socket
    _callback_map = {}

    def __init__(self, addr: str, port: int = 5050, mode: SocketMode = SocketMode.UNIX_DOMAIN_SOCKET):
        """
        Initializes the client.

        :param str addr: the addr of the socket to use. This can be a file path for Unix-Domain-Sockets or an
        ip-address for INET-Sockets. (e.g. ./uds_socket or 127.0.0.1)
        :param int port: The port to use if a INET-Socket is used, ignored otherwise. Default: 5050
        :param SocketMode mode: The mode of the socket (UNIX_DOMAIN_SOCKET or INET_SOCKET). Default: UNIX_DOMAIN_SOCKET
        """
        self._sock_addr = addr
        self._sock_port = port
        self._sock_mode = mode

    def start(self):
        """
        Starts the client and creates the socket (based on which mode was chosen during init).
        Will try and connect to the broker and start the message receive thread.
        """
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
        """
        Sends a string message to the specified channel.

        :param str channel: The channel the message will be send to.
        :param str message: The message that will be send.
        :param bool exclude_self: If True, the client sending the message will not receive it via the channel it is
        send to, even if he is subscribed. Default: True
        """
        data = {'msg_type': MessageType.DATA_MESSAGE, 'channel': channel, 'message': message,
                'exclude_self': exclude_self}
        data_to_send = json.dumps(data).encode('utf-8')
        socket_util.send_data(self._sock, data_to_send)

    def subscribe(self, channel: str, callback: Callable):
        """
        Subscribes to a specified channel.

        :param str channel: Name of the channel to subscribe to
        :param Callable callback: A callable with one parameter (the received message) that will be called when a
        message is received on the specified channel.
        """
        channel_subscribe_data = {'msg_type': MessageType.SUBSCRIBE_MESSAGE, 'channel': channel}
        data_to_send = json.dumps(channel_subscribe_data).encode('utf-8')
        socket_util.send_data(self._sock, data_to_send)
        self._register_message_received_callback(channel, callback)

    def _register_message_received_callback(self, channel: str, callback: Callable):
        """
        Internal method to map a callback to a specified channel.

        :param str channel: The channel to map the callback to
        :param Callable callback: The callback to map to the channel.
        """
        if channel in self._callback_map:
            self._callback_map[channel].append(callback)
        else:
            self._callback_map[channel] = [callback]

    def _on_message_received(self, msg: bytes):
        """
        Internal method that calls all registered callbacks when a message is received.

        :param bytes msg: The received JSON message as bytes.
        """
        decoded_data = json.loads(msg)
        channel = decoded_data['channel']
        if channel in self._callback_map:
            for callback in self._callback_map[channel]:
                callback(decoded_data)

    def _read_thread(self):
        """
        Internal method that represents the read thread. Will read data packets from the client socket.
        """
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
