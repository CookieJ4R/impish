# impish - Interprocess communication made easy!

impish (**i**nterprocess **m**essage **p**assing **i**s **s**imple enoug**h**) is a library to simplify interprocess communication. Inspired by MQTT it comes with two classes:
- ImpishBroker
- ImpishClient

that work with the publish/subscribe pattern. On Unix they use a Unix-domain socket to communicate. On windows you´ll have to use a INET socket.

