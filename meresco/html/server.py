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
from meresco.components.http import ObservableHttpServer, ApacheLogger, PathFilter, FileServer, PathRename, SessionHandler
from weightless.io import Reactor
from weightless.core import compose, be
from sys import stdout
from os.path import join

from .dynamichtml import DynamicHtml
from .login import BasicHtmlLoginForm, PasswordFile, SecureZone

def dna(reactor, port, dynamic, static, data, verbose=True):
    apacheLogger = ApacheLogger(stdout) if verbose else ApacheLogger()

    basicHtmlLoginForm = BasicHtmlLoginForm(action="/login.action", loginPath="/secure/login") 
    passwordFile = PasswordFile(join(data, "passwd"))

    secureDynamic = join(dynamic, "secure")

    return (Observable(),
        (ObservableHttpServer(reactor, port=port),
            (apacheLogger,
                (SessionHandler(), 
                    (PathFilter('/static'),
                        (PathRename(lambda path: path[len('/static'):]),
                            (FileServer(static),)
                        )
                    ),
                    (PathFilter('/secure', excluding=['/static']),
                        (SecureZone("/secure/login"),
                            (DynamicHtml([secureDynamic], reactor=reactor, indexPage='/secure/index', prefix="/secure", verbose=True), 
                                (basicHtmlLoginForm,
                                    (passwordFile, )
                                )
                            ),
                        )
                    ),
                    (PathFilter('/', excluding=['/static', '/secure', '/login.action']),
                        (DynamicHtml([dynamic], reactor=reactor, indexPage='/index'),)
                    ),
                    (PathFilter('/login.action'),
                        (basicHtmlLoginForm, )
                    )
                )
            )
        )
    )

def startServer(**kwargs):
    reactor = Reactor()

    server = be(dna(reactor=reactor, **kwargs))
    list(compose(server.once.observer_init()))

    print("Ready to rumble at", kwargs['port'])
    reactor.loop()

