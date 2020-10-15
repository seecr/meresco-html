## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2019 SURF https://surf.nl
# Copyright (C) 2019-2020 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Html"
#
# "Meresco Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import os
from os import makedirs, remove, listdir
from os.path import isdir, join
from hashlib import md5
from seecr.zulutime import ZuluTime
from pprint import pprint
from meresco.core import Observable
try:
    from gustos.common.units import COUNT
except ImportError:
    COUNT = 'count'

TESTMODE = os.environ.get('TESTMODE', '').upper() == 'TRUE'

class ErrorLog(object):
    def __init__(self, directory, logtofile=not TESTMODE, maxSize=1000, response=None):
        self._logtofile = logtofile
        self._directory = directory
        isdir(self._directory) or makedirs(self._directory)
        self._maxSize = maxSize
        self._nrOfErrors = 0
        self._nrOfFiles = self._rotate()
        self._errorHandlingResponse = response

    def logError(self, traceback, *args, **kwargs):
        self._nrOfErrors += 1
        if self._logtofile:
            with open(join(self._directory, self._filename()), "w") as fp:
                fp.write("Args: \n")
                pprint(args, stream=fp)
                fp.write("\nKWargs: \n")
                pprint(kwargs, stream=fp)
                fp.write("\nTraceback:\n")
                fp.write(str(traceback))
                fp.write("\n - End of Traceback -\n")
            self._nrOfFiles = self._rotate()
        else:
            print(traceback)

    def errorHandlingHook(self, traceback, *args, **kwargs):
        self.logError(traceback, *args, **kwargs)
        return self._errorHandlingResponse

    def _filename(self):
        return '{}.error.txt'.format(ZuluTime().iso8601basic())

    def _rotate(self):
        l = listdir(self._directory)
        if len(l) > self._maxSize:
            # do not rotate every time we are on the edge, clean up a bit mor.
            for f in sorted(l)[:-int(self._maxSize * 4/5)]:
                remove(join(self._directory, f))
        return len(l)

    def getFilesAndErrors(self):
        return self._nrOfFiles, self._nrOfErrors

class ErrorLogReport(Observable):
    def __init__(self, name=None):
        Observable.__init__(self, name=name)

    def handleReport(self):
        nrOfFiles, nrOfErrors = self.call.getFilesAndErrors()
        self.do.report(values={self.observable_name():{"Errors":{
            "files":{COUNT: nrOfFiles},
            "errors": {COUNT: nrOfErrors},
            }}})
        return
        yield

