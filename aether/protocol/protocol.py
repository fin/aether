from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import  reactor
import base64
import json
import os, os.path

from aexceptions import *

class AetherTransferServer(LineReceiver):
    """ listen and receive files:
        * first get metadata line [size; filename] as json
        * then switch to raw mode & receive the file
    """

    def __init__(self):
        self.fp = None
        self.absolute_filename = None
        self.receivedBytes = 0

    def connectionMade(self):
        print 'got connection'
        pass

    def _mkValidFilename(self):
        if not os.path.abspath(self.absolute_filename).startswith(os.path.abspath(self.factory.baseDir)):
            raise AeInvalidFilenameException(self.filename)

        if not os.access(self.absolute_filename, os.F_OK):
            return self.absolute_filename
        else:
            for x in xrange(2,100):
                newpath = u'%s%d' % (self.absolute_filename, x)
                if not os.access(newpath, os.F_OK):
                    return newpath
            raise AeInvalidFilenameException(self.filename)

    def _openFile(self):
        self.fp = open(self.absolute_filename, 'w')

    def lineReceived(self, line):
        print line
        d = json.loads(base64.decodestring(line))
        self.filesize = d['size']
        self.filename = d['name']
        self.absolute_filename = os.path.join(self.factory.baseDir, self.filename)
        try:
            print self.absolute_filename
            self.absolute_filename = self._mkValidFilename()
            print self.absolute_filename
        except Exception, e:
            self.absolute_filename = None
            self.transport.loseConnection()
            raise e
        self._openFile()

        self.receivedBytes = 0

        self.setRawMode()

    def rawDataReceived(self, data):
        print data
        self.fp.write(data)
        self.receivedBytes += len(data)
        if self.receivedBytes > self.filesize:
            raise AeInvalidFilesizeException(self.receivedBytes, self.filesize)
        
        self.factory.progressCallback(self.filename, self.receivedBytes, self.filesize)


    def connectionLost(self, reason):
        print 'done'
        print self.receivedBytes
        if self.fp:
            try:
                self.fp.close()
            except Exception, e:
                print e
        
        if self.absolute_filename and os.path.getsize(self.absolute_filename) != self.filesize:
            raise AeInvalidFilesizeException(self.filesize, os.path.getsize(self.absolute_filename))
        print reason

class AetherTransferServerFactory(Factory):
    protocol = AetherTransferServer

    def __init__(self, baseDir, progressCallback=None):
        if not os.path.isdir(baseDir) or not os.access(baseDir, os.O_RDWR):
            raise AeNoDirectoryException(baseDir)
        self.baseDir = baseDir
        self.progressCallback = progressCallback or (lambda *x:x)


class AetherTransferClient(Protocol):
    """ send a file to a server:
        * first: metadata (base64; json-encoded)
        * rawmode: file data
    """

    def _mkHeaders(self, filename):
        return  {'name': os.path.split(filename)[1],
                 'size': os.path.getsize(filename)}

    def sendFile(self, filename):
        self.fp = open(filename, 'r')
        self.sentBytes = 0

        d = self._mkHeaders(filename)

        self.transport.write(base64.encodestring(json.dumps(d)))
        self.transport.write('\r\n')

        for chunk in self.fp.read(4096):
            self.transport.write(chunk)
            self.sentBytes += len(chunk)

        self.transport.loseConnection()

    def connectionLost(self, reason):
        print reason
        reactor.stop()

