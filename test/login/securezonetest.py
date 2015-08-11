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

from meresco.html.login import SecureZone

class SecureZoneTest(SeecrTestCase):

    def testSecureZone(self):
        secureZone = SecureZone('/page_with_login')
        root = Observable()
        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = ''.join(compose(root.all.handleRequest(path='/secret_page', query='a=b', session=session, arguments={})))

        self.assertEquals(redirectHttp % '/page_with_login', response)
        self.assertEquals(0, len(observer.calledMethods))
        self.assertEquals({'originalPath':'/secret_page?a=b', 'BasicHtmlLoginForm.formValues':{'errorMessage': 'Login required for "/secret_page".'}}, session)

    def testSecureZoneWithoutQuery(self):
        secureZone = SecureZone('/page_with_login', defaultLanguage="nl")
        root = Observable()
        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/secret_page', query='', session=session, arguments={}))

        self.assertEquals(redirectHttp % '/page_with_login', response)
        self.assertEquals(0, len(observer.calledMethods))
        self.assertEquals({'originalPath':'/secret_page', 'BasicHtmlLoginForm.formValues': {'errorMessage': 'Inloggen verplicht voor "/secret_page".'}}, session)

    def testSecureZoneAllowed(self):
        secureZone = SecureZone('/page_with_login')

        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)

        root = Observable()
        root.addObserver(secureZone)

        user = CallTrace('user')

        response = asString(root.all.handleRequest(path='/secret_page', query='a=b', session={'user':user}, arguments={}))

        self.assertEquals(1, len(observer.calledMethods))
        self.assertEquals('/secret_page', observer.calledMethods[0].kwargs['path'])
        self.assertEquals('a=b', observer.calledMethods[0].kwargs['query'])
        self.assertEquals({'user':user}, observer.calledMethods[0].kwargs['session'])

    def testAllowedInsecurePages(self):
        secureZone = SecureZone('/page_with_login', excluding=['/allowed'])
        root = Observable()
        observer = CallTrace('Observer', returnValues={'handleRequest' :(f for f in ['HTTP/1.0 200 OK\r\n\r\nBody'])})
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/allowed_page', query='a=b', session=session, arguments={}))

        self.assertEquals('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())
        self.assertEquals({}, session)

    def testAllowedInsecurePagesForLoginPage(self):
        secureZone = SecureZone('/page_with_login', excluding=['/allowed'])
        root = Observable()
        observer = CallTrace('Observer', 
            returnValues={'handleRequest' :(f for f in ['HTTP/1.0 200 OK\r\n\r\nBody'])})
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/page_with_login', query='a=b', session=session, arguments={}))

        self.assertEquals('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())
        self.assertEquals({}, session)

    def testRememberMeCookie(self):

        paths = []
        def handleRequest(path, *args, **kwargs):
            paths.append(path)
            yield "RESPONSE"
        
        observer = CallTrace(methods={'handleRequest': handleRequest}) 
        def validateRememberMeCookie(cookie):
            return "USER" if cookie == "THIS IS THE REMEMBER ME COOKIE" else None

        dna = be(
            (Observable(),
                (SecureZone(
                    "/page_with_login", 
                    excluding=['/allowed'],
                    rememberMeCookieName="CID",
                    rememberMeCookieMethod=validateRememberMeCookie
                    ),
                    (observer, ) 
                )
            ))
        session = {}
        response = asString(dna.all.handleRequest(
            path='/some_page', 
            query='',
            arguments={},
            session=session))
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /page_with_login\r\n\r\n", response)
        self.assertEquals([], paths)
        self.assertFalse('user' in session, session)

        session = {}
        response = asString(dna.all.handleRequest(
            path='/some_page', 
            query='',
            arguments={},
            Headers=dict(Cookie="CID=THIS IS THE REMEMBER ME COOKIE"),
            session=session))
        self.assertEquals("RESPONSE", response)
        self.assertEquals(['/some_page'], paths)
        self.assertTrue('user' in session, session)

