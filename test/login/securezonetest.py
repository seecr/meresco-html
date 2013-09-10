## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2005-2010 Seek You Too B.V. (CQ2) http://www.cq2.nl
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

from meresco.core import Observable
from weightless.core import compose
from meresco.components.http.utils import redirectHttp

from seecr.test import CallTrace, SeecrTestCase

from seecr.html.login import SecureZone

class SecureZoneTest(SeecrTestCase):

    def testSecureZone(self):
        secureZone = SecureZone('/page_with_login')
        root = Observable()
        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = ''.join(compose(root.all.handleRequest(path='/secret_page', query='a=b', session=session)))

        self.assertEquals(redirectHttp % '/page_with_login', response)
        self.assertEquals(0, len(observer.calledMethods))
        self.assertEquals({'originalPath':'/secret_page?a=b', 'BasicHtmlLoginForm.formValues':{'errorMessage': 'Login required for "/secret_page"'}}, session)

    def testSecureZoneWithoutQuery(self):
        secureZone = SecureZone('/page_with_login')
        root = Observable()
        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = ''.join(compose(root.all.handleRequest(path='/secret_page', query='', session=session)))

        self.assertEquals(redirectHttp % '/page_with_login', response)
        self.assertEquals(0, len(observer.calledMethods))
        self.assertEquals({'originalPath':'/secret_page', 'BasicHtmlLoginForm.formValues': {'errorMessage': 'Login required for "/secret_page"'}}, session)

    def testSecureZoneAllowed(self):
        secureZone = SecureZone('/page_with_login')

        observer = CallTrace('Observer', emptyGeneratorMethods=['handleRequest'])
        secureZone.addObserver(observer)

        root = Observable()
        root.addObserver(secureZone)

        user = CallTrace('user')

        list(compose(root.all.handleRequest(path='/secret_page', query='a=b', session={'user':user})))

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

        response = ''.join(compose(root.all.handleRequest(path='/allowed_page', query='a=b', session=session)))

        self.assertEquals('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())
        self.assertEquals({}, session)

    def testAllowedInsecurePagesForLoginPage(self):
        secureZone = SecureZone('/page_with_login', excluding=['/allowed'])
        root = Observable()
        observer = CallTrace('Observer', returnValues={'handleRequest' :(f for f in ['HTTP/1.0 200 OK\r\n\r\nBody'])})
        secureZone.addObserver(observer)
        root.addObserver(secureZone)
        session={}

        response = ''.join(compose(root.all.handleRequest(path='/page_with_login', query='a=b', session=session)))

        self.assertEquals('HTTP/1.0 200 OK\r\n\r\nBody', response)
        self.assertEquals(['handleRequest'], observer.calledMethodNames())
        self.assertEquals({}, session)
