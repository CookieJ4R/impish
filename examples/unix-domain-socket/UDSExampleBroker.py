import time

from impish import ImpishBroker

if __name__ == '__main__':
    broker = ImpishBroker(addr="./impish_uds")
    broker.start()
    while True:
        time.sleep(100)
