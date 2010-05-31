#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferClient
from twisted.internet import reactor, threads
from twisted.internet.protocol import ClientCreator


def send(x):
    reactor.callLater(1, x.sendFile, '/home/fin/Mixotic_200_-_Anonymous_-_200_9_hours.mp3')

if __name__ == '__main__':
    c = ClientCreator(reactor, AetherTransferClient)
   
    x = c.connectTCP('localhost', 9999)
    x.addCallback(send)
    reactor.run()

