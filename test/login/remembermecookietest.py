## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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
from weightless.core import compose, consume, be, asString
from meresco.components.http.utils import redirectHttp

from seecr.test import CallTrace, SeecrTestCase

from meresco.html.login import RememberMeCookie

class RememberMeCookieTest(SeecrTestCase):

    def testRememberMeCookie(self):

        paths = []
        def handleRequest(path, *args, **kwargs):
            paths.append(path)
            yield "RESPONSE"
        
        def validateMethod(cookie):
            return "USER" if cookie == "THIS IS THE REMEMBER ME COOKIE" else None

        observer = CallTrace(methods={
            'handleRequest': handleRequest, 
            'validateCookie': validateMethod}) 

        dna = be(
            (Observable(),
                (RememberMeCookie(cookieName="CID"),
                    (observer, ) 
                )
            ))
        session = {}
        response = asString(dna.all.handleRequest(
            path='/some_page', 
            session=session))
        self.assertEquals("RESPONSE", response)
        self.assertEquals(['/some_page'], paths)
        self.assertFalse('user' in session, session)

        paths = []
        session = {}
        response = asString(dna.all.handleRequest(
            path='/some_page', 
            Headers=dict(Cookie="CID=THIS IS THE REMEMBER ME COOKIE"),
            session=session))
        self.assertEquals("RESPONSE", response)
        self.assertEquals(['/some_page'], paths)
        self.assertTrue('user' in session, session)

