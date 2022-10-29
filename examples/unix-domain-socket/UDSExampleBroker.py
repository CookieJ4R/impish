import time

from impish import ImpishBroker

"""
Example for using the ImpishBroker with an UNIX_DOMAIN_SOCKET.
"""

if __name__ == '__main__':
    broker = ImpishBroker(addr="./impish_uds")
    broker.start()

    # continue with your program...
    while True:
        time.sleep(100)
