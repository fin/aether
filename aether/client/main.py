#!/usr/bin/python

""" ohlol """

import sys, math

from twisted.internet import reactor

from aether.protocol.protocol import AetherTransferClient
from twisted.internet.protocol import ClientCreator
import pybonjour
import time
import select
from optparse import OptionParser
from datetime import datetime, timedelta




regtype = u'_at_nomin_aether._tcp'
timeout = 5
resolved = {}

class Sender(object):
    def __init__(self, filename, end_callback):
        self.filename = filename
        import progressbar
        self.pb = progressbar.ProgressBar().start()
        self.pbcur= 0
        self.cb = end_callback
    def send(self, x):
        x.end_callback = self.cb
        reactor.callLater(1, x.sendFile, self.filename, self.callback)

    def callback(self, done, full):
        newval = math.floor(done/full*self.pb.maxval)
        if self.pbcur != newval:
            self.pbcur= newval
            self.pb.update(self.pbcur)


def resolve_callback(addcallback, serviceName, regtype, replyDomain, sdRef, flags, interfaceIndex, errorCode, fullname,
                        hosttarget, port, txtRecord):
    if errorCode:
        print errorCode
        return
    resolved[serviceName] = 'lol'
    addcallback(serviceName=serviceName, regtype=regtype, replyDomain=replyDomain, sdRef=sdRef, flags=flags, interfaceIndex=interfaceIndex,
            errorCode=errorCode, fullname=fullname, hosttarget=hosttarget, port=port,
            txtRecord=txtRecord)


def resolve(addcallback, serviceName, regtype, interfaceIndex=0, replyDomain=None):
    replyDomain = replyDomain or 'local.'

    def cb(*x, **y):
        return resolve_callback(addcallback, serviceName, regtype, replyDomain, *x, **y)

    resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                    interfaceIndex,
                                                    serviceName,
                                                    regtype,
                                                    replyDomain,
                                                    cb)
    try:
        try:
            del resolved[serviceName]
        except Exception, e:
            pass
        while not serviceName in resolved:
            ready = select.select([resolve_sdRef], [], [], 1)
            if resolve_sdRef not in ready[0]:
                print 'Resolve timed out'
                break
            pybonjour.DNSServiceProcessResult(resolve_sdRef)
    finally:
        resolve_sdRef.close()



def browse_callback(addcallback, removecallback, sdRef, flags, interfaceIndex, errorCode, serviceName,
                            regtype, replyDomain):
    if errorCode  != pybonjour.kDNSServiceErr_NoError:
        print 'what'
        print errorCode
        return
    if not (flags & pybonjour.kDNSServiceFlagsAdd):
        removecallback(serviceName=serviceName, regtype=regtype, replyDomain=replyDomain)
        return

    return resolve(addcallback, serviceName, regtype, interfaceIndex, replyDomain)


def browse(regtype, addcallback, removecallback, timeout=lambda: False):


    browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype,
            callBack = lambda *x, **y: browse_callback(addcallback, removecallback, *x, **y))

    if not callable(timeout):
        end = datetime.now() + timedelta(seconds=timeout)
        timeout = lambda: datetime.now()>end

    while not timeout():
        ready = select.select([browse_sdRef], [], [], 1) 
        if browse_sdRef in ready[0]:
            pybonjour.DNSServiceProcessResult(browse_sdRef)
    print 'done'


def send(target, filename, end_callback=lambda *x, **y: False, lookupDomain=''):
    def send_actual(**kwargs):
        c = ClientCreator(reactor, AetherTransferClient)
        x = c.connectTCP(kwargs['hosttarget'], kwargs['port'])
        x.addCallback(Sender(filename, end_callback).send)
    resolve(send_actual, target, regtype, 0, lookupDomain)

if __name__ == '__main__':
    do = sys.argv[1]
    if do=='send':
        target = sys.argv[2]
        filename = sys.argv[3]
        print (target, filename)
        send(target, filename)
        reactor.run()


    if do=='list':
        d = {}
        browse(regtype,
                lambda serviceName, regtype, replyDomain, *a, **b: d.__setitem__((serviceName, regtype, replyDomain,), (a, b)),
                lambda serviceName, regtype, replyDomain: d.__delitem__((serviceName, regtype, replyDomain,)),
                timeout)
        print d

    if do=='ui':
        print 'ohlol'

