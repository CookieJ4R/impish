import json
import os
import socket
import threading
from json import JSONDecodeError

from impish.util import socket_util
from impish.util.MessageType import MessageType
from impish.util.SocketMode import SocketMode


class ImpishBroker:
    _sock: socket.socket
    _communication_threads = []
    _channel_client_map = {}

    _should_accept_clients = threading.Event()

    def __init__(self, addr: str, port: int = 5050, mode: SocketMode = SocketMode.UNIX_DOMAIN_SOCKET):
        self._sock_addr = addr
        self._socket_port = port
        self._socket_mode = mode

    def start(self):
        if self._socket_mode == SocketMode.UNIX_DOMAIN_SOCKET:
            self._try_unlink(self._sock_addr)
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
        while self._should_accept_clients.is_set():
            client, _ = self._sock.accept()
            client_communication_thread = threading.Thread(target=self._client_read_thread, args=[client], daemon=True)
            self._communication_threads.append(client_communication_thread)
            client_communication_thread.start()

    def _client_read_thread(self, client: socket.socket):
        try:
            while True:
                try:
                    packet_data_length = client.recv(4)
                    if not packet_data_length:
                        break
                    packet_data_length = int.from_bytes(packet_data_length, byteorder="little")
                    data = client.recv(packet_data_length)
                    self._on_client_data_received(client, data)
                    if not data:
                        break
                except ConnectionResetError:
                    for channel_name in self._channel_client_map.keys():
                        if client in self._channel_client_map[channel_name]:
                            self._channel_client_map[channel_name].remove(client)
                    break
        finally:
            client.close()

    def _on_client_data_received(self, client: socket.socket, data):
        try:
            data = json.loads(data)
            if data['msg_type'] == MessageType.SUBSCRIBE_MESSAGE:
                self._add_client_to_channel(data['channel'], client)
            elif data['msg_type'] == MessageType.DATA_MESSAGE:
                self._forward_message_to_clients(client, data)
        except JSONDecodeError:
            raise

    def _add_client_to_channel(self, channel: str, client: socket.socket):
        if channel in self._channel_client_map:
            self._channel_client_map[channel].append(client)
        else:
            self._channel_client_map[channel] = [client]

    def _forward_message_to_clients(self, src_client, data):
        channel = data['channel']
        if channel in self._channel_client_map:
            for client in self._channel_client_map[channel]:
                if data['exclude_self'] and src_client == client:
                    continue
                if not socket_util.send_data(client, json.dumps(data).encode('utf-8')):
                    self._channel_client_map[channel].remoce(client)

    @staticmethod
    def _try_unlink(addr: str):
        try:
            os.unlink(addr)
        except OSError:
            if os.path.exists(addr):
                raise
