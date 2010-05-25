#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferClient
from twisted.internet import reactor, threads
from twisted.internet.protocol import ClientCreator


def send(x):
    x.sendFile('protocol/test/test1.txt')

if __name__ == '__main__':
    c = ClientCreator(reactor, AetherTransferClient)
   
    x = c.connectTCP('localhost', 9999)
    x.addCallback(send)
    reactor.run()

