#!/usr/bin/python

""" ohlol """

import sys, math

if sys.argv[1]=='ui':
    from twisted.internet import gtk2reactor # for gtk-2.0
    gtk2reactor.install()
from twisted.internet import reactor, threads

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
    def __init__(self, filename):
        self.filename = filename
        import progressbar
        self.pb = progressbar.ProgressBar().start()
        self.pbcur= 0
    def send(self, x):
        reactor.callLater(1, x.sendFile, self.filename, self.callback)
    def callback(self, done, full):
        newval = math.floor(done/full*self.pb.maxval)
        if self.pbcur != newval:
            self.pbcur= newval
            self.pb.update(self.pbcur)


def resolve_callback(addcallback, serviceName, sdRef, flags, interfaceIndex, errorCode, fullname,
                        hosttarget, port, txtRecord):
    if errorCode:
        print errorCode
        return
    resolved[serviceName] = 'lol'
    addcallback(serviceName=serviceName, sdRef=sdRef, flags=flags, interfaceIndex=interfaceIndex,
            errorCode=errorCode, fullname=fullname, hosttarget=hosttarget, port=port,
            txtRecord=txtRecord)


def resolve(addcallback, serviceName, regtype, interfaceIndex=0, replyDomain=''):
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



def browse_callback(addcallback, removecallback, sdRef, flags, interfaceIndex, errorCode, serviceName,
                            regtype, replyDomain):
    if errorCode  != pybonjour.kDNSServiceErr_NoError:
        print 'what'
        print errorCode
        return
    if not (flags & pybonjour.kDNSServiceFlagsAdd):
        removecallback(serviceName=serviceName)
        return

    return resolve(addcallback, serviceName, regtype, interfaceIndex, replyDomain)


def browse(regtype, addcallback, removecallback, timeout=lambda: False):


    browse_sdRef = pybonjour.DNSServiceBrowse(regtype = regtype,
            callBack = lambda *x, **y: browse_callback(addcallback, removecallback, *x, **y))

    if not callable(timeout):
        end = datetime.now() + timedelta(seconds=timeout)
        timeout = lambda: datetime.now()>end

    while not timeout():
        ready = select.select([browse_sdRef], [], [], 10) 
        if browse_sdRef in ready[0]:
            pybonjour.DNSServiceProcessResult(browse_sdRef)


def send(target, filename):
    def send_actual(**kwargs):
        c = ClientCreator(reactor, AetherTransferClient)
       
        x = c.connectTCP(kwargs['hosttarget'], 9999)
        x.addCallback(Sender(filename).send)
        reactor.run()
    resolve(send_actual, target, regtype)

if __name__ == '__main__':
    do = sys.argv[1]
    if do=='send':
        target = sys.argv[2]
        filename = sys.argv[3]
        send(target, filename)


    if do=='list':
        d = {}
        browse(regtype, lambda serviceName, *a, **b: d.__setitem__(serviceName, (a, b)), lambda serviceName: d.__delitem__(serviceName), timeout)
        print d

    if do=='ui':
        print 'ohlol'
        import gtk
        quit = gtk.ImageMenuItem('gtk-quit')
        quit.connect('activate', gtk.main_quit)

        si = gtk.status_icon_new_from_file('statusicon.png')
        menu = gtk.Menu()
        menu.append(quit)
        menu.show_all()
        si.connect('popup-menu', lambda tray, button, time: menu.popup(None, None, None, button, time))
        reactor.run()

