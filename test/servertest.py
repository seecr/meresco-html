# -*- coding: utf-8 -*-
## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2013 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import join

from weightless.core import compose
from seecr.test import SeecrTestCase
from seecr.html.server import handler

def serialize(generator):
    return "".join(compose(generator))

class ServerTest(SeecrTestCase):

    def testOne(self):
        open(join(self.tempdir, "tst"), "w").write("hello!")
        h = handler(self.tempdir, "/dyn", "index.html", "/s", "/d")
        x = h.all.handleRequest(path="/s/tst")
        self.assertTrue("hello!" in serialize(x))

