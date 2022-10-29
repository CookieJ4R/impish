import time

from impish import ImpishBroker
from impish import SocketMode

if __name__ == '__main__':
    broker = ImpishBroker(addr="127.0.0.1", port=5050, mode=SocketMode.INET_SOCKET)
    broker.start()
    while True:
        time.sleep(100)
