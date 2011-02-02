#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferServerFactory
from twisted.internet import reactor, threads

import time
import sys
import pybonjour


class Lol:
    def __init__(self):
        self.last_received = 0

    def cb(self, client, name, received, total, failed=False):
        if failed:
            print "%s failed :/" % name
            return
        promille = total / 1000
        if promille < 4096:
            promille = 4096
        if self.last_received + promille < received:
            self.last_received = received
            print (self.last_received, received)

class Service(object):
    def __init__(self, name, path, cbhandler, endcb=None):
        self.regtype = u'_at_nomin_aether._tcp'
        self.name = name
        self.path = path
        self.port = 9999
        self.cbhandler = cbhandler
        self.endcb = endcb

    def listen(self):
        factory = AetherTransferServerFactory(self.path, self.cbhandler)
        self.port = reactor.listenTCP(0, factory).getHost().port
        self.sdRef = pybonjour.DNSServiceRegister(name = self.name,
                                             regtype = self.regtype,
                                             port = self.port,
                                             callBack = lambda **x: x)
    def stop(self):
        self.sdRef.close()


if __name__ == '__main__':
    x = None
    try:
        l = Lol()
        x = Service('fin' if len(sys.argv)<2 else sys.argv[1], '/tmp', l.cb)
        x.listen()
        reactor.run()
    finally:
        if x:
            x.stop()

