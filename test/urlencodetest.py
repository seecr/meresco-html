# -*- encoding: utf-8 -*-
## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2013 Seecr (Seek You Too B.V.) http://seecr.nl
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
from seecr.html import urlencode
from urllib import urlencode as urllib_urlencode

class UrlencodeTest(SeecrTestCase):

    def testDict(self):
        self.assertEquals('a=a%3Fp', urlencode({'a': 'a?p'}))
        self.assertEquals('a=a%3Fp&a=fiets', urlencode({'a': ['a?p', 'fiets']}))

    def testUnicode(self):
        self.assertEquals('a=a%3Fp', urlencode({'a': u'a?p'}))
        self.assertEquals('a=a%C3%A1p', urlencode({'a': 'a\xc3\xa1p'}))
        self.assertEquals('a=a%C3%A1p', urlencode({'a': 'aáp'}))
        self.assertEquals('a=a%C3%A1p', urlencode({'a': u'aáp'}))

    def testUnicodeTupleList(self):
        self.assertEquals('a=a%3Fp', urlencode([('a', u'a?p')]))
        self.assertEquals('a=a%C3%A1p', urlencode([('a', 'a\xc3\xa1p')]))
        self.assertEquals('a=a%C3%A1p', urlencode([('a', 'aáp')]))
        self.assertEquals('a=a%C3%A1p', urlencode([('a', u'aáp')]))

    def testIntegerInUrlencode(self):
        self.assertEquals('a=3', urlencode({'a': 3}))

    def testUnicodeBugInDefaultUnicode(self):
        self.assertEquals('a=a%3Fp', urllib_urlencode({'a': u'a?p'}))
        self.assertEquals('a=3', urllib_urlencode({'a': 3}))
        self.assertEquals('a=a%C3%A1p', urllib_urlencode({'a': 'a\xc3\xa1p'}))
        self.assertEquals('a=a%C3%A1p', urllib_urlencode({'a': 'aáp'}))
        self.assertEquals('a=a%C3%A1p', urllib_urlencode({'a': u'aáp'}))
        self.assertEquals('a=a%3Fp', urllib_urlencode({'a': u'a?p'}, doseq=True))
        self.assertEquals('a=a%C3%A1p', urllib_urlencode({'a': 'a\xc3\xa1p'}, doseq=True))
        self.assertEquals('a=a%C3%A1p', urllib_urlencode({'a': 'aáp'}, doseq=True))
        # Bug in unicode characters and us of doseq=True
        self.assertEquals('a=a%3Fp', urllib_urlencode({'a': u'aáp'}, doseq=True))


