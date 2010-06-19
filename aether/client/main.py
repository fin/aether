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

def resolve_callback(addcallback, serviceName, sdRef, flags, interfaceIndex, errorCode, fullname,
                        hosttarget, port, txtRecord):
    if errorCode:
        print errorCode
        return
    addcallback(serviceName=serviceName, sdRef=sdRef, flags=flags, interfaceIndex=interfaceIndex,
            errorCode=errorCode, fullname=fullname, hosttarget=hosttarget, port=port,
            txtRecord=txtRecord)



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

        def browse_callback(addcallback, removecallback, sdRef, flags, interfaceIndex, errorCode, serviceName,
                                    regtype, replyDomain):
            if errorCode  != pybonjour.kDNSServiceErr_NoError:
                print 'what'
                print errorCode
                return
            if not (flags & pybonjour.kDNSServiceFlagsAdd):
                removecallback(serviceName=serviceName)
                return

            resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                            interfaceIndex,
                                                            serviceName,
                                                            regtype,
                                                            replyDomain,
                                                            lambda *x, **y: resolve_callback(addcallback, serviceName, *x, **y))
            try:
                while not serviceName in resolved:
                    ready = select.select([resolve_sdRef], [], [], 1)
                    if resolve_sdRef not in ready[0]:
                        print 'Resolve timed out'
                        break
                    pybonjour.DNSServiceProcessResult(resolve_sdRef)
            finally:
                resolve_sdRef.close()

        d = {}

        browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype,
                callBack = lambda *x, **y: browse_callback(lambda serviceName, *a, **b: d.__setitem__(serviceName, (a, b)), lambda serviceName: d.__delitem__(serviceName), *x, **y))

        end = datetime.now() + timedelta(seconds=10)

        while(datetime.now()<end):
            ready = select.select([browse_sdRef], [], [], 10) 
            if browse_sdRef in ready[0]:
                pybonjour.DNSServiceProcessResult(browse_sdRef)
            print d
            time.sleep(0.5)


