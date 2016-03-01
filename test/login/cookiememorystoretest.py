## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase
from meresco.html.login.cookiememorystore import CookieMemoryStore
from time import sleep

class CookieMemoryStoreTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.d = CookieMemoryStore(0.1)

    def testCookieName(self):
        name = self.d.cookieName()
        self.assertTrue(name.startswith('remember-'))
        self.assertEquals(name, self.d.cookieName())
        self.assertNotEqual(name, CookieMemoryStore().cookieName())

    def testCreateCookie(self):
        result = self.d.createCookie('username')
        self.assertEquals('username', self.d.validateCookie(result['value']))
        self.assertNotEqual(result, self.d.createCookie('username'))
        self.assertEquals(self.d.cookieName(), result['name'])
        self.assertEquals(0.1, result['expires'])
        sleep(0.06)
        self.assertEquals('username', self.d.validateCookie(result['value']))
        sleep(0.06)
        self.assertEquals('username', self.d.validateCookie(result['value']))
        sleep(0.12)
        self.assertEquals(None, self.d.validateCookie(result['value']))

    def testCreateCookieForAnyObject(self):
        o = object()
        result = self.d.createCookie(o)
        self.assertEquals(o, self.d.validateCookie(result['value']))
