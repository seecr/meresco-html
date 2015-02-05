# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2012, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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


from os.path import join, abspath, dirname

from seecr.test.integrationtestcase import IntegrationState as _IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator

mypath = dirname(abspath(__file__))
docDir = '/usr/share/doc/python3-meresco-html'
docDir = join(dirname(dirname(mypath)), 'doc') #DO_NOT_DISTRIBUTE

class IntegrationState(_IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        _IntegrationState.__init__(self, "meresco-html-server-"+stateName, tests=tests, fastMode=fastMode)

        self.port = PortNumberGenerator.next()

    def binDir(self):
        binDir = '/usr/bin'
        binDir = join(dirname(dirname(mypath)), 'bin') #DO_NOT_DISTRIBUTE
        return binDir

    def setUp(self):
        self._startServer('server', self.binPath('meresco-html-server-py3'), 'http://localhost:%s/' % self.port, 
            port=self.port, 
            dynamic=join(docDir, 'example', 'dynamic'), 
            static=join(docDir, 'example', 'static'),
            data=self.integrationTempdir)

