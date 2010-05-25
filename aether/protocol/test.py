#!/usr/bin/python
import os
import protocol
import json, base64
from twisted.trial import unittest
from twisted.test import proto_helpers
import aexceptions

class ClientTestCase(unittest.TestCase):
    testfile = os.path.join(os.path.dirname(os.path.abspath(globals()["__file__"])), 'test/test1.txt')

    def setUp(self):
        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.proto = protocol.AetherTransferClient()
        self.tr.protocol = self.proto
        self.proto.makeConnection(self.tr)

    def test_header(self):
        d = self.proto._mkHeaders(self.testfile)
        self.assertEqual(d['size'], os.path.getsize(self.testfile))
        self.assertEqual(d['name'], 'test1.txt')

    def test_send(self):
        self.proto.sendFile(self.testfile)
        self.assertEquals(self.tr.value(), 'eyJuYW1lIjogInRlc3QxLnR4dCIsICJzaXplIjogMTZ9\n\r\nohaithar\nohlol.\n')


class ServerTestCase(unittest.TestCase):
    testfile = os.path.join(os.path.dirname(os.path.abspath(globals()["__file__"])), 'test/test1.txt')

    def setUp(self):
        self.baseDir = os.tmpnam()
        os.mkdir(self.baseDir)

        factory = protocol.AetherTransferServerFactory(self.baseDir)
        self.tr = proto_helpers.StringTransportWithDisconnection()
        self.proto = factory.buildProtocol(('127.0.0.1', 0))
        self.tr.protocol = self.proto
        self.proto.makeConnection(self.tr)

    def test_receive(self):
        self.proto.dataReceived('eyJuYW1lIjogInRlc3QxLnR4dCIsICJzaXplIjogMTZ9\n\r\nohaithar\nohlol.\n')
        self.assert_(self.proto.receivedBytes)
        self.tr.loseConnection()
    
    def test_receive_head_fail(self):
        self.assertRaises(Exception, self.proto.dataReceived, 'eyuYW1lIjogInRlc3QxLnR4dCIsICJzaXplIjogMTZ9\n\r\nohaithar\nohlol.\n')
        self.tr.loseConnection()
    
    def test_receive_filename_fail(self):
        d = {'name': '../../ohlol', 'size': -1}
        self.assertRaises(aexceptions.AeInvalidFilenameException, self.proto.dataReceived, '%s\n\r\nohaithar\nohlol.\n' % base64.encodestring(json.dumps(d)))
        self.proto.absolute_filename = None
        self.tr.loseConnection()
    
    def test_receive_filesize_negative(self):
        d = {'name': 'ohlol', 'size': -1}
        self.assertRaises(aexceptions.AeInvalidFilesizeException, self.proto.dataReceived, '%s\n\r\nohaithar\nohlol.\n' % base64.encodestring(json.dumps(d)))
        self.assertRaises(aexceptions.AeInvalidFilesizeException, self.tr.loseConnection)

    def test_receive_filesize_toohigh(self):
        d = {'name': 'ohlol', 'size': 1}
        self.assertRaises(aexceptions.AeInvalidFilesizeException, self.proto.dataReceived, '%s\n\r\nohaithar\nohlol.\n' % base64.encodestring(json.dumps(d)))
        self.assertRaises(aexceptions.AeInvalidFilesizeException, self.tr.loseConnection)
    
    def test_receive_filesize_toohigh(self):
        d = {'name': 'ohlol', 'size': 1123}
        self.proto.dataReceived('%s\n\r\nohaithar\nohlol.\n' % base64.encodestring(json.dumps(d)))
        self.assertRaises(aexceptions.AeInvalidFilesizeException, self.tr.loseConnection)

    def tearDown(self):
        if hasattr(self.proto, 'absolute_filename') and self.proto.absolute_filename:
            os.remove(self.proto.absolute_filename)
        os.rmdir(self.baseDir)

