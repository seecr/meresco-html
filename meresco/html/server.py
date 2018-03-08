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

from meresco.core import Observable
from meresco.components.http import ObservableHttpServer, PathFilter, FileServer, PathRename, BasicHttpHandler
from meresco.components.log import ApacheLogWriter, LogCollector, HandleRequestLog
from weightless.io import Reactor
from weightless.core import compose, be
from sys import stdout

from dynamichtml import DynamicHtml

def dna(reactor, port, dynamic, static, verbose=True):
    return (Observable(),
        (ObservableHttpServer(reactor, port=port),
            (LogCollector(),
                (ApacheLogWriter(stdout if verbose else None), ),
                (HandleRequestLog(),
                    (BasicHttpHandler(),
                        (PathFilter('/static'),
                            (PathRename(lambda path: path[len('/static'):]),
                                (FileServer(static),)
                            )
                        ),
                        (PathFilter('/', excluding=['/static']),
                            (DynamicHtml([dynamic], reactor=reactor, indexPage='/index'),)
                        )
                    )
                )
            )
        )
    )

def startServer(**kwargs):
    reactor = Reactor()

    server = be(dna(reactor=reactor, **kwargs))
    list(compose(server.once.observer_init()))

    print "Ready to rumble at", kwargs['port']
    reactor.loop()

