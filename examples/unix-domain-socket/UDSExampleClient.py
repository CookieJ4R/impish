import os
import time

from impish import ImpishClient

"""
Example for using the ImpishClient with an UNIX_DOMAIN_SOCKET.
"""


def on_msg_callback(msg):
    """
    Callback that gets called when a message is received.
    """
    print(f"Received message: {msg['message']} on channel {msg['channel']}")


if __name__ == '__main__':
    client = ImpishClient(addr="./impish_uds")
    client.start()
    client.subscribe("test_channel", on_msg_callback)

    # continue with your program...
    while True:
        client.send_data("test_channel", f"This is client with pid {os.getpid()}")
        time.sleep(10)
