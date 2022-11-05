import json
import socket
import threading
from json import JSONDecodeError
from typing import Dict

from impish.util import socket_util
from impish.util.MessageType import MessageType
from impish.util.SocketMode import SocketMode
from impish.util.socket_util import try_unlink


class ImpishBroker:
    """
    The ImpishBroker is responsible for receiving messages from the connected clients and distributing them via the
    channels.
    """

    _sock: socket.socket
    _communication_threads = []
    _channel_client_map = {}

    _should_accept_clients = threading.Event()

    def __init__(self, addr: str, port: int = 5050, mode: SocketMode = SocketMode.UNIX_DOMAIN_SOCKET):
        """
        Initializes the client.

        :param str addr: the addr of the socket to use. This can be a file path for Unix-Domain-Sockets or an
        ip-address for INET-Sockets. (e.g. ./uds_socket or 127.0.0.1)
        :param int port: The port to use if a INET-Socket is used, ignored otherwise. Default: 5050
        :param SocketMode mode: The mode of the socket (UNIX_DOMAIN_SOCKET or INET_SOCKET). Default: UNIX_DOMAIN_SOCKET
        """
        self._sock_addr = addr
        self._socket_port = port
        self._socket_mode = mode

    def start(self):
        """
        Starts the broker and creates the socket (based on which mode was chosen during init).
        Will also start a thread on which client connections are accepted.
        """
        if self._socket_mode == SocketMode.UNIX_DOMAIN_SOCKET:
            try_unlink(self._sock_addr)
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.bind(self._sock_addr)
        elif self._socket_mode == SocketMode.INET_SOCKET:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.bind((self._sock_addr, self._socket_port))
        self._sock.listen()
        self._should_accept_clients.set()
        client_accept_thread = threading.Thread(target=self._accept_clients, daemon=True)
        client_accept_thread.start()

    def _accept_clients(self):
        """
        This method runs on the thread that will listen for new connecting clients and accept them.
        If a client connects a separate client thread is spawned that will handle communication with this new client.
        """
        while self._should_accept_clients.is_set():
            client, _ = self._sock.accept()
            client_communication_thread = threading.Thread(target=self._client_read_thread, args=[client], daemon=True)
            self._communication_threads.append(client_communication_thread)
            client_communication_thread.start()

    def _client_read_thread(self, client: socket.socket):
        """
        This method runs on the respective client communication thread spawned when the client got accepted.
        Responsible for receiving data from the connected clients.
        """
        try:
            while True:
                try:
                    packet_data_length = client.recv(4)
                    if not packet_data_length:
                        break
                    packet_data_length = int.from_bytes(packet_data_length, byteorder="little")
                    data = client.recv(packet_data_length)
                    self._on_client_msg_received(client, data)
                    if not data:
                        break
                except ConnectionResetError:
                    for channel_name in self._channel_client_map.keys():
                        if client in self._channel_client_map[channel_name]:
                            self._channel_client_map[channel_name].remove(client)
                    break
        finally:
            client.close()

    def _on_client_msg_received(self, client: socket.socket, msg: bytes):
        """
        Internal method that determines the type of the message and acts accordingly.
        If the message is a subscribe message, the client will be registered to the channel specified in it.
        If the message is a data message the message will be forwarded to all clients subscribed to the channel
        the message is addressed to.

        :param socket.socket client: The client from which the data was received.
        :param bytes msg: The received JSON message as bytes.
        """
        try:
            data = json.loads(msg)
            if data['msg_type'] == MessageType.SUBSCRIBE_MESSAGE:
                self._add_client_to_channel(data['channel'], client)
            elif data['msg_type'] == MessageType.UNSUBSCRIBE_MESSAGE:
                self._remove_client_from_channel(data['channel'], client)
            elif data['msg_type'] == MessageType.DATA_MESSAGE:
                self._forward_message_to_clients(client, data)
        except JSONDecodeError:
            raise

    def _add_client_to_channel(self, channel: str, client: socket.socket):
        """
        Internal method that maps a client to a specified channel.

        :param str channel: The channel to map the client to.
        :param socket.socket client: The client to map to the channel.
        """
        if channel in self._channel_client_map:
            self._channel_client_map[channel].append(client)
        else:
            self._channel_client_map[channel] = [client]

    def _remove_client_from_channel(self, channel: str, client: socket.socket):
        """
        Internal method that removes a client from a specified channel.

        :param str channel: The channel to remove the client from.
        :param socket.socket client: The client to remove from the channel.
        """
        if channel in self._channel_client_map:
            self._channel_client_map[channel].remove(client)

    def _forward_message_to_clients(self, src_client: socket.socket, msg: Dict):
        """
        Internal method that forwards a message to all clients subscribed to the channel over which the message was
        sent.

        :param socket.socket src_client: The client over which the message was sent. Used to ignore the client during
        message forwarding if wanted by the client that sent the message.
        :param Dict msg: The parsed message that should be forwarded to all clients subscribed to the channel specified
        by the message.
        """
        channel = msg['channel']
        if channel in self._channel_client_map:
            for client in self._channel_client_map[channel]:
                if msg['exclude_self'] and src_client == client:
                    continue
                if not socket_util.send_data(client, json.dumps(msg).encode('utf-8')):
                    self._channel_client_map[channel].remove(client)
