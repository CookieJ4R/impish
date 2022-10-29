import os
import time

from impish import ImpishClient


def on_msg_callback(msg):
    print(f"Received message: {msg['message']} on channel {msg['channel']}")


if __name__ == '__main__':
    client = ImpishClient(addr="./impish_uds")
    client.start()
    client.subscribe("test_channel", lambda msg: on_msg_callback(msg))
    while True:
        client.send_data("test_channel", f"This is client with pid {os.getpid()}")
        time.sleep(10)
