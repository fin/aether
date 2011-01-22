import gtk
import pynotify
import sys
import copy
import signal


sys.path.append('..')

from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()
from twisted.internet import reactor, threads
from aether.client.main import browse, resolve, send
from aether.server.main import Service

import urllib, os

regtype = u'_at_nomin_aether._tcp'


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
        run.remove('lol')
        reactor.callFromThread(gtk.main_quit)
        reactor.callFromThread(reactor.stop)
    except Exception, e:
        print e


builder = gtk.Builder()
builder.add_from_file("glade/glaether.glade")
builder.connect_signals({ "on_window_destroy" : ui_quit })
window = builder.get_object('window')
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
    def __init__(self, to, parent_widget, uri):
        self.to = to
        self.parent_widget = parent_widget
        self.uri = uri

        self.widget = get_widget('transfer')

    def progress(self, done, full):
        fraction= float(done)/float(full)
        gtk.idle_add(self.widget.get_children()[0].set_fraction, fraction)
        gtk.idle_add(self.widget.get_children()[1].set_text, str(fraction))



def thing_dropped(serviceName, widget, context, x, y, selection, target_type, timestamp):
    if target_type == TARGET_TYPE_URI_LIST:
        uri = selection.data.strip('\r\n\x00')
        print 'uri', uri
        uri_splitted = uri.split() # we may have more than one file dropped
        for uri in uri_splitted:
            path = get_file_path_from_dnd_dropped_uri(uri)
            if os.path.isfile(path): # is it file?
                transfer = Transfer(to=serviceName, parent_widget=widget, uri=uri)
                reactor.callInThread(send, serviceName, path, lambda *x, **y: False, '', transfer.progress)
                widget.pack_start(transfer.widget, False, True)
                
        context.finish(True, False, timestamp)
        return True
    return False

def ui_add(serviceName, regtype, replyDomain, *a, **b):
    k = (serviceName, regtype, replyDomain,)
    if not k in services:
        mi = gtk.MenuItem(serviceName)
        mi.connect('activate', lambda _: ui_click(services[k]))
        menu.append(mi)
        menu.show_all()
        x = get_widget('recipient')
        x.get_children()[0].set_text(serviceName)

        discovered.pack_start(x, False, True)

        x.connect('drag_motion', motion_cb)
        x.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, [('text/uri-list', 0, TARGET_TYPE_URI_LIST,) ], gtk.gdk.ACTION_COPY)
        x.connect('drag_data_received', lambda *args, **kwargs: thing_dropped(serviceName, *args, **kwargs))


        services[k]={'k': k, 'data1': a, 'data2': b, 'menu_item': mi}


def ui_remove(serviceName, regtype, replyDomain):
    k = (serviceName, regtype, replyDomain,)
    try:
        menu.remove(services[k]['menu_item'])
        del services[k]
    except Exception, e:
        print e


class ReceiveHandler(object):
    def __init__(self):
        self.last_received = 0
        self.transfers = {}

    def cb(self, name, received, total):
        ui = self.transfers.get(name, None) or pynotify.Notification(name)
        ui.set_timeout(1)
        self.transfers[name]=ui
        promille = total / 1000
        if promille < 4096:
            promille = 4096
        if self.last_received + promille < received:
            self.last_received = received
            ui.update(name, '%d / %d' % (received, total))
            ui.show()
        if self.last_received==total:
            ui.update(name, '%d / %d' % (received, total))
            ui.show()
            del self.transfers[name]

            


rh = ReceiveHandler()
service = Service('finui@finkpad', '/tmp', rh.cb)




quit.connect('activate', ui_quit)

reactor.callInThread(browse, regtype, ui_add, ui_remove, lambda: not run)

reactor.callInThread(service.listen)
reactor.run()

