# -*- encoding: utf-8 -*-
## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2013-2014 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.html import urlencode
from urllib.parse import urlencode as urllib_urlencode

class UrlencodeTest(SeecrTestCase):

    def testDict(self):
        self.assertEqual('a=a%3Fp', urlencode({'a': 'a?p'}))
        self.assertEqual('a=a%3Fp&a=fiets', urlencode({'a': ['a?p', 'fiets']}))

    def testUnicode(self):
        self.assertEqual('a=a%3Fp', urlencode({'a': 'a?p'}))
        self.assertEqual('a=a%C3%A1p', urlencode({'a': 'aáp'}))

    def testUnicodeTupleList(self):
        self.assertEqual('a=a%3Fp', urlencode([('a', 'a?p')]))
        self.assertEqual('a=a%C3%A1p', urlencode([('a', 'aáp')]))

    def testIntegerInUrlencode(self):
        self.assertEqual('a=3', urlencode({'a': 3}))

    def testUnicodeBugInDefaultUnicode(self):
        self.assertEqual('a=a%3Fp', urllib_urlencode({'a': 'a?p'}))
        self.assertEqual('a=3', urllib_urlencode({'a': 3}))
        self.assertEqual('a=a%C3%A1p', urllib_urlencode({'a': 'aáp'}))
        self.assertEqual('a=a%C3%A1p', urllib_urlencode({'a': 'aáp'}))
        self.assertEqual('a=a%3Fp', urllib_urlencode({'a': 'a?p'}, doseq=True))
        self.assertEqual('a=a%C3%A1p', urllib_urlencode({'a': 'aáp'}, doseq=True))

