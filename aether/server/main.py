#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferServerFactory
from twisted.internet import reactor, threads

import time

class Lol:
    def __init__(self):
        self.last_received = 0

    def cb(self, name, received, total):
        promille = total / 1000
        if promille < 4096:
            promille = 4096
        if self.last_received + promille < received:
            self.last_received = received
            print (self.last_received, received)

l = Lol()

if __name__ == '__main__':
    factory = AetherTransferServerFactory('/tmp', l.cb)
    reactor.listenTCP(9999, factory)
    reactor.run()

