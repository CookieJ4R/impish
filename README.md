# impish - Interprocess communication made easy!

    pip install impish

impish (**i**nterprocess **m**essage **p**assing **i**s **s**imple enoug**h**) is a library to simplify interprocess communication. Inspired by MQTT it comes with two classes:
- ImpishBroker
- ImpishClient

that work with the publish/subscribe pattern. On Unix they use a Unix-domain socket to communicate. On Windows you´ll have to use a INET socket.
You can however also use an INET socket on Unix if you wish. Using a Inet socket should also allow IPC between separate machines. Unix-domain sockets however can only be used locally.

## Getting started

To learn how to use impish have a look at the provided examples [here](/examples).

## Tests

Complete tests will (probably) be provided in a later release.
