#!/usr/bin/python

class AeNoDirectoryException(Exception):
    def __init__(self, directory):
        self.directory = directory

    def __repr__(self):
        return u'%s / %s'%(super(AeNoDirectoryException, self).__repr__(), self.directory)

class AeInvalidFilenameException(Exception):
    def __init__(self, filename):
        self.filename = filename
    def __repr__(self):
        return u'%s / %s'%(super(AeInvalidFilenameException, self).__repr__(), self.directory)


class AeInvalidFilesizeException(Exception):
    def __init__(self, size1, size2):
        self.size1 = size1
        self.size2 = size2

    def __repr(self):
        return u'%s / %s,%s'%(super(AeInvalidFilenameException, self).__repr__(),
                self.size1, self.size2)
