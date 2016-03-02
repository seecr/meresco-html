## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.core import Observable
from weightless.core import be, asString

from seecr.test import CallTrace, SeecrTestCase

from meresco.html.login import RememberMeCookie

class RememberMeCookieTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.paths = []
        def handleRequest(path, *args, **kwargs):
            self.paths.append(path)
            yield "RESPONSE"
        def validateMethod(cookie):
            return "USER" if cookie == "THIS IS THE REMEMBER ME COOKIE" else None
        observer = CallTrace(methods={
            'handleRequest': handleRequest,
            'validateCookie': validateMethod,
            'cookieName': lambda: "CID"})
        self.dna = be(
            (Observable(),
                (RememberMeCookie(),
                    (observer, )
                )
            ))

    def testNoCookie(self):
        session = {}
        response = asString(self.dna.all.handleRequest(
            path='/some_page',
            Headers={},
            session=session))
        self.assertEquals("RESPONSE", response)
        self.assertEquals(['/some_page'], self.paths)
        self.assertFalse('user' in session, session)

    def testCookie(self):
        session = {}
        response = asString(self.dna.all.handleRequest(
            path='/some_page',
            Headers=dict(Cookie="CID=THIS IS THE REMEMBER ME COOKIE"),
            session=session))
        self.assertEquals("RESPONSE", response)
        self.assertEquals(['/some_page'], self.paths)
        self.assertTrue('user' in session, session)

