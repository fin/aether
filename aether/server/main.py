#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferServerFactory
from twisted.internet import reactor, threads

import time

def cb(name, received, total):
    print name
    print received
    print total
    print '---'

if __name__ == '__main__':
    factory = AetherTransferServerFactory('/tmp', cb)
    reactor.listenTCP(9999, factory)
    reactor.run()

