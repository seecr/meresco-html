## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Seecr Html"
# 
# "Seecr Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Seecr Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Seecr Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from meresco.core import Observable, Transparent
from meresco.components.http import ObservableHttpServer, ApacheLogger, PathFilter, FileServer, PathRename
from weightless.io import Reactor
from weightless.core import compose, be
from sys import stdout

from dynamichtml import DynamicHtml

#class ObservableDirectoryWatcher(Observable):
#    """Idee to get rid of events sources in handlers"""
#    def __init__(self, reactor, directory, handlerName):
#        dirWatcher = DirectoryWatcher(directory,
#                self._notifyHandler,
#                CreateFile=True, ModifyFile=True, MoveInFile=True)
#        reactor.addReader(dirWatcher, dirWatcher)
#        self._handlerName = handlerName
#
#    def _notifyHandler(self, event):
#        self.do.unknown(self.handlerName, event)

def bear(dna):
    being = be(dna)
    list(compose(being.once.observer_init()))
    return being

def httpserver(reactor, port=None, verbose=None, **kwargs):
    hook = Transparent()
    dna = \
        (Observable(),
            (ObservableHttpServer(reactor, port=port),
                (ApacheLogger(stdout) if verbose else ApacheLogger(),
                    (hook,)
                )
            )
        )
    return bear(dna), hook

def handler(static, dynamic, index, staticpath, dynpath, **kwargs):
    dna = \
            (Transparent(),
                (PathFilter(staticpath), #, excluding=[dynpath]),
                    (PathRename(lambda path: path[len(staticpath):]),
                        (FileServer(static),)
                    ),
                ),
                (PathFilter(dynpath, excluding=[staticpath]),
                        #(PathRename(lambda path: path[len(dynpath):]),
                        (DynamicHtml([dynamic], indexPage=index),)
                        #),
                ),
            )
    return bear(dna)

def startServer(**kwargs):
    reactor = Reactor()
    server, hook = httpserver(reactor, **kwargs)
    hook.addObserver(handler(**kwargs))
    print "Ready to rumble at", kwargs['port']
    reactor.loop()

