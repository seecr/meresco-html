## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2014, 2020 Seecr (Seek You Too B.V.) http://seecr.nl
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

        self.assertEqual(redirectHttp % '/page_with_login', response)
        self.assertEqual(0, len(observer.calledMethods))
        self.assertEqual({'originalPath':'/secret_page?a=b', 'BasicHtmlLoginForm.formValues':{'errorMessage': 'Login required for "/secret_page".'}}, session)

    def testSecureZoneWithoutQuery(self):
        secureZone = SecureZone('/page_with_login', defaultLanguage="nl")
        root = Observable()
        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/secret_page', query='', session=session, arguments={}))

        self.assertEqual(redirectHttp % '/page_with_login', response)
        self.assertEqual(0, len(observer.calledMethods))
        self.assertEqual({'originalPath':'/secret_page', 'BasicHtmlLoginForm.formValues': {'errorMessage': 'Inloggen verplicht voor "/secret_page".'}}, session)

    def testSecureZoneAllowed(self):
        secureZone = SecureZone('/page_with_login')

        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)

        root = Observable()
        root.addObserver(secureZone)

        user = CallTrace('user')

        response = asString(root.all.handleRequest(path='/secret_page', query='a=b', session={'user':user}, arguments={}))

        self.assertEqual(1, len(observer.calledMethods))
        self.assertEqual('/secret_page', observer.calledMethods[0].kwargs['path'])
        self.assertEqual('a=b', observer.calledMethods[0].kwargs['query'])
        self.assertEqual({'user':user}, observer.calledMethods[0].kwargs['session'])

    def testAllowedInsecurePages(self):
        secureZone = SecureZone('/page_with_login', excluding=['/allowed'])
        root = Observable()
        observer = CallTrace('Observer', returnValues={'handleRequest' :(f for f in ['HTTP/1.0 200 OK\r\n\r\nBody'])})
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/allowed_page', query='a=b', session=session, arguments={}))

        self.assertEqual('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEqual(['handleRequest'], observer.calledMethodNames())
        self.assertEqual({}, session)

    def testAllowedInsecurePagesForLoginPage(self):
        secureZone = SecureZone('/page_with_login', excluding=['/allowed'])
        root = Observable()
        observer = CallTrace('Observer', 
            returnValues={'handleRequest' :(f for f in ['HTTP/1.0 200 OK\r\n\r\nBody'])})
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = asString(root.all.handleRequest(path='/page_with_login', query='a=b', session=session, arguments={}))

        self.assertEqual('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEqual(['handleRequest'], observer.calledMethodNames())
        self.assertEqual({}, session)

