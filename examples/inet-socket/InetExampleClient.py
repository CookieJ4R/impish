import os
import time

from impish import ImpishClient
from impish import SocketMode

"""
Example for using the ImpishClient with an INET_SOCKET.
"""


def on_msg_callback(msg):
    """
    Callback that gets called when a message is received.
    """
    print(f"Received message: {msg['message']} on channel {msg['channel']}")


if __name__ == '__main__':
    client = ImpishClient(addr="127.0.0.1", port=5050, mode=SocketMode.INET_SOCKET)
    client.start()
    client.subscribe("test_channel", on_msg_callback)

    # continue with your program...
    while True:
        client.send_data("test_channel", f"This is client with pid {os.getpid()}")
        time.sleep(10)
