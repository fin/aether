#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferServerFactory
from twisted.internet import reactor, threads

import time
import pybonjour

regtype = u'_at_nomin_aether._tcp'
name = 'fin@finkpad'
port = 9999

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
sdRef = None

if __name__ == '__main__':
    try:
        factory = AetherTransferServerFactory('/tmp', l.cb)
        reactor.listenTCP(port, factory)
        sdRef = pybonjour.DNSServiceRegister(name = name,
                                             regtype = regtype,
                                             port = port,
                                             callBack = lambda **x: x)
        reactor.run()
    finally:
        if sdRef:
            sdRef.close()

