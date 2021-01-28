## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2014, 2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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
            return dict(value="USER", header="COOKIE HEADER") if cookie == "THIS IS THE REMEMBER ME COOKIE" else None
        self.observer = CallTrace(methods={
            'handleRequest': handleRequest,
            'validateCookie': validateMethod,
            'cookieName': lambda: "CID"})
        self.dna = be(
            (Observable(),
                (RememberMeCookie(),
                    (self.observer, )
                )
            ))

    def testNoCookie(self):
        session = {}
        response = asString(self.dna.all.handleRequest(
            path='/some_page',
            Headers={},
            session=session))
        self.assertEqual("RESPONSE", response)
        self.assertEqual(['/some_page'], self.paths)
        self.assertFalse('user' in session, session)
        self.assertEqual(['cookieName', 'handleRequest'], self.observer.calledMethodNames())
        self.assertEqual({'path': '/some_page', 'session': {}, 'Headers':{}}, self.observer.calledMethods[-1].kwargs)

    def testCookie(self):
        session = {}
        Headers=dict(Cookie="CID=THIS IS THE REMEMBER ME COOKIE")
        response = asString(self.dna.all.handleRequest(
            path='/some_page',
            Headers=Headers,
            session=session))
        self.assertEqual("RESPONSE", response)
        self.assertEqual(['/some_page'], self.paths)
        self.assertTrue('user' in session, session)
        self.assertEqual(['cookieName', 'validateCookie', 'handleRequest'], self.observer.calledMethodNames())
        self.assertEqual({'path': '/some_page', 'session': {'user':'USER'}, 'Headers':Headers}, self.observer.calledMethods[-1].kwargs)

