#!/usr/bin/python

""" ohlol """

from aether.protocol.protocol import AetherTransferClient
from twisted.internet import reactor, threads
from twisted.internet.protocol import ClientCreator

import pybonjour
import time
import select

from optparse import OptionParser

import sys
from datetime import datetime, timedelta


regtype = u'_at_nomin_aether._tcp'
timeout = 5
resolved = {}

class Sender(object):
    def __init__(self, filename):
        self.filename = filename
    def send(self, x):
        reactor.callLater(1, x.sendFile, self.filename)

def resolve_callback(serviceName, sdRef, flags, interfaceIndex, errorCode, fullname,
                        hosttarget, port, txtRecord):
    if errorCode:
        print errorCode
        return
    resolved[serviceName] = (fullname, hosttarget, port, txtRecord)
    print resolved[serviceName]



if __name__ == '__main__':
    do = sys.argv[1]
    if do=='send':
        target = sys.argv[2]
        filename = sys.argv[3]
        
        c = ClientCreator(reactor, AetherTransferClient)
       
        x = c.connectTCP('localhost', 9999)
        x.addCallback(Sender(filename).send)
        reactor.run()


    if do=='list':

        def browse_callback(sdRef, flags, interfaceIndex, errorCode, serviceName,
                                    regtype, replyDomain):
            if errorCode:
                print 'what'
                print errorCode
                return
            resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                            interfaceIndex,
                                                            serviceName,
                                                            regtype,
                                                            replyDomain,
                                                            lambda *x, **y: resolve_callback(serviceName, *x, **y))
            try:
                while not serviceName in resolved:
                    ready = select.select([resolve_sdRef], [], [])
                    if resolve_sdRef not in ready[0]:
                        print 'Resolve timed out'
                        break
                    pybonjour.DNSServiceProcessResult(resolve_sdRef)
            finally:
                resolve_sdRef.close()

        browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype,
                                                          callBack = browse_callback)

        end = datetime.now() + timedelta(seconds=10)

        while(datetime.now()<end):
            ready = select.select([browse_sdRef], [], [], 10) 
            if browse_sdRef in ready[0]:
                pybonjour.DNSServiceProcessResult(browse_sdRef)
            time.sleep(0.5)
                    

