from twisted.internet import gtk2reactor # for gtk-2.0
gtk2reactor.install()
from twisted.internet import reactor, threads
from aether.client.main import browse, resolve, send
from aether.server.main import Service

import gtk
import pynotify

regtype = u'_at_nomin_aether._tcp'


services = {}
run = ['lol']

quit = gtk.ImageMenuItem('gtk-quit')


si = gtk.status_icon_new_from_file('statusicon.png')
menu = gtk.Menu()
menu.append(quit)
menu.show_all()
si.connect('popup-menu', lambda tray, button, time: menu.popup(None, None, None, button, time))
si.connect('activate', lambda _: menu.popup(None, None, None, 0, 0))

def ui_click(service):
     dialog = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
             buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
     dialog.set_default_response(gtk.RESPONSE_OK)
     response = dialog.run()
     if response == gtk.RESPONSE_OK:
         reactor.callInThread(send, service['k'][0], dialog.get_filename(), lambda:True, service['k'][2])
     dialog.destroy()

def ui_add(serviceName, regtype, replyDomain, *a, **b):
    k = (serviceName, regtype, replyDomain,)
    if not k in services:
        mi = gtk.MenuItem(serviceName)
        mi.connect('activate', lambda _: ui_click(services[k]))
        menu.append(mi)
        menu.show_all()
        services[k]={'k': k, 'data1': a, 'data2': b, 'mi': mi}
def ui_remove(serviceName, regtype, replyDomain):
    k = (serviceName, regtype, replyDomain,)
    try:
        menu.remove(services[k]['mi'])
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


def ui_quit(*a,**b):
    run.remove('lol')
    service.stop()
    reactor.callFromThread(reactor.stop)
    reactor.callFromThread(gtk.main_quit)


quit.connect('activate', ui_quit)

reactor.callInThread(browse, regtype, ui_add, ui_remove, lambda: not run)

reactor.callInThread(service.listen)
reactor.run()

