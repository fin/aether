import gtk
import gobject
import pynotify
import sys
import copy
import signal
import socket

import getpass


sys.path.append('..')

from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()
from twisted.internet import reactor, threads
from aether.client.main import browse, resolve, send
from aether.server.main import Service

import urllib, os

regtype = u'_at_nomin_aether._tcp'
SERVICENAME = '%s@%s' % (getpass.getuser(), socket.gethostname(),) 


services = {}

run = ['lol'] # this is a way ugly hack.

quit = gtk.ImageMenuItem('gtk-quit')


si = gtk.status_icon_new_from_file('statusicon.png')
menu = gtk.Menu()
menu.append(quit)
menu.show_all()



TARGET_TYPE_URI_LIST = 80


def ui_quit(*a,**b):
    try:
        print 'quitting'
        try:
            run.remove('lol')
        except Exception, e:
            print e
        try:
            reactor.callFromThread(gtk.main_quit)
        except Exception, e:
            gtk.main_quit()
            print e
        try:
            reactor.callFromThread(reactor.stop)
        except Exception, e:
            print e
    except Exception, e:
        print e


builder = gtk.Builder()
builder.add_from_file("glade/glaether.glade")
builder.connect_signals({ "on_window_destroy" : ui_quit })
window = builder.get_object('window')
window.set_title('aether')

window.get_children()[0].get_children()[1].get_children()[0].modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0xaaaaaa,0xaaaaaa,0xaaaaaa))
window.get_children()[0].get_children()[0].get_children()[0].set_text(SERVICENAME)
window.get_children()[0].get_children()[0].get_children()[1].set_text("Receiving to ~/Downloads")

discovered = builder.get_object('discovered')
window.show()


signal.signal(signal.SIGINT, ui_quit)


def get_widget(name):
    builder = gtk.Builder()
    builder.add_from_file("glade/glaether.glade")
    return builder.get_object(name)


def hidewin(x):
    print 'hiding window'
    window.hide()



def show(lol):
    print 'showing window'
    window.visible = True
    window.height = 500

si.connect('popup-menu', lambda tray, button, time: menu.popup(None, None, None, button, time))
si.connect('activate', show)

def ui_click(service):
     dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
             buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
     dialog.set_default_response(gtk.RESPONSE_OK)
     response = dialog.run()
     if response == gtk.RESPONSE_OK:
         reactor.callInThread(send, service['k'][0], dialog.get_filename(), lambda:True, service['k'][2])
     dialog.destroy()


def get_file_path_from_dnd_dropped_uri(uri):
    # get the path to file
    path = ""
    if uri.startswith('file:\\\\\\'): # windows
        path = uri[8:] # 8 is len('file:///')
    elif uri.startswith('file://'): # nautilus, rox
        path = uri[7:] # 7 is len('file://')
    elif uri.startswith('file:'): # xffm
        path = uri[5:] # 5 is len('file:')

    path = urllib.url2pathname(path) # escape special chars
    path = path.strip('\r\n\x00') # remove \r\n and NULL

    return path

def motion_cb(wid, context, x, y, time):
    context.drag_status(gtk.gdk.ACTION_COPY, time)
    return True

class Transfer(object):
    def __init__(self, peer, parent_widget, uri):
        self.peer = peer
        self.parent_widget = parent_widget
        self.uri = uri
        self.sender = None
        self.cancelled = False

        self.widget = get_widget('transfer')
        self.progresswidget = self.widget.get_children()[0].get_children()[0].get_children()[0]
        self.stopimage = self.widget.get_children()[0].get_children()[0].get_children()[1]
        gobject.idle_add(self.progresswidget.set_text, uri.split('/')[-1])


        self.stopimage.connect('clicked', self.cancel)

    def progress(self, done, full):
        fraction= float(done)/float(full)
        gobject.idle_add(self.progresswidget.set_fraction, fraction)
        if done == full:
            gobject.idle_add(self.parent_widget.remove, self.widget)
            pynotify.Notification('%s done' % self.uri.split('/')[-1]).show()

    def failed(self):
        gobject.idle_add(self.parent_widget.remove, self.widget)
        pynotify.Notification('%s failed' % self.uri.split('/')[-1]).show()

    def cancel(self, sender):
        print 'transfer: cancel! %s' % self.sender
        self.cancelled = True
        if self.sender:
            self.sender.cancel()

def transfer_over(service, transfer, failed=None):
    gobject.idle_add(transfer.parent_widget.remove, transfer.widget)

def send_thing(transfer, *args, **kwargs):
    print 'sending thing'
    transfer.sender = send(*args, **kwargs)


def thing_dropped(service, widget, context, x, y, selection, target_type, timestamp):
    if target_type == TARGET_TYPE_URI_LIST:
        uri = selection.data.strip('\r\n\x00')
        print 'uri', uri
        uri_splitted = uri.split() # we may have more than one file dropped
        for uri in uri_splitted:
            path = get_file_path_from_dnd_dropped_uri(uri)
            if os.path.isfile(path): # is it file?
                transfer = Transfer(peer=service, parent_widget=widget, uri=uri)
                gobject.idle_add(widget.pack_start, transfer.widget, False, True)
                service['transfers'].append(transfer)
                reactor.callInThread(send_thing, transfer, service['k'][0], path, lambda *x, **y: transfer_over(service, transfer), '', transfer.progress)
                
        context.finish(True, False, timestamp)
        return True
    return False

def ui_add(serviceName, regtype, replyDomain, hosttarget, *a, **b):
    print hosttarget
    k = (serviceName, regtype, replyDomain,)
    if serviceName == SERVICENAME:
        print 'ignoring %s' % serviceName
        return
    if not k in services:
        mi = gtk.MenuItem(serviceName)
        mi.connect('activate', lambda _: ui_click(services[k]))
        menu.append(mi)
        menu.show_all()
        x = get_widget('recipient')
        x.get_children()[0].set_text(serviceName)
        x.connect('drag_motion', motion_cb)


        x.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, [('text/uri-list', 0, TARGET_TYPE_URI_LIST,) ], gtk.gdk.ACTION_COPY)

        services[k]={'k': k, 'data1': a, 'data2': b, 'menu_item': mi, 'ip': socket.gethostbyname(hosttarget), 'transfers': [], 'listitem': x,}
        x.connect('drag_data_received', lambda *args, **kwargs: thing_dropped(services[k], *args, **kwargs))
        
        gobject.idle_add(discovered.pack_start, x, False, True)




def ui_remove(serviceName, regtype, replyDomain):
    k = (serviceName, regtype, replyDomain,)
    try:
        gobject.idle_add(menu.remove, services[k]['menu_item'])
        gobject.idle_add(discovered.remove, services[k]['listitem'])
        del services[k]
    except Exception, e:
        print e


class ReceiveHandler(object):
    def __init__(self):
        self.last_received = 0
        self.transfers = {}

    def cb(self, client, name, received, total, failed=False, server=None):
        service = None
        for s in services.values():
            if s['ip']==client[0]:
                service = s
                break

    
        try:
            if service:
                transfers = [x for x in s['transfers'] if x.uri==name]
                if not transfers:
                    transfer = Transfer(peer=s, parent_widget=s['listitem'], uri=name)
                    s['transfers'].append(transfer)
                    gobject.idle_add(s['listitem'].pack_start, transfer.widget, False, True)
                else:
                    transfer = transfers[0]
                
                if transfer.cancelled:
                    server.transport.loseConnection()

                if not failed:
                    gobject.idle_add(transfer.progress, received, total)
                else:
                    gobject.idle_add(transfer.failed)
            else:
                pass
        except Exception, e:
            print e

    def cb_fail(self, client, name, failed):
        pass



rh = ReceiveHandler()

service = Service(SERVICENAME, os.path.expanduser('~/Downloads'), rh.cb)




quit.connect('activate', ui_quit)

reactor.callInThread(browse, regtype, ui_add, ui_remove, lambda: not run)

reactor.callInThread(service.listen)
reactor.run()

