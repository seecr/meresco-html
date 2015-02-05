## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test.integrationtestcase import IntegrationTestCase
from seecr.test.utils import getRequest, headerToDict, postRequest

from urllib.parse import urlencode

class ServerTest(IntegrationTestCase):
    def testServer(self):
        header, body = getRequest(path='/', port=self.port, parse=False)
        headers = headerToDict(header)
        self.assertEqual(set(['Location', 'Set-Cookie']), headers.keys())
        self.assertEqual("/index", headers['Location'])
        self.assertTrue(header.startswith("HTTP/1.0 302 Found"), header)

    def testExamplePage(self):
        header, body = getRequest(path='/example', port=self.port, parse=False)
        self.assertTrue(' 200 ' in header, header)
        self.assertTrue('<img src="/static/seecr-logo-smaller.png">' in body, body)

    def testStatic(self):
        header, body = getRequest(path='/static/seecr-logo-smaller.png', port=self.port, parse=False)
        self.assertTrue(' 200 ' in header, header)
        self.assertTrue('Content-Type: image/png' in header, header)

    def testRedirectedToLogin(self):
        header, body = getRequest(path='/secure', port=self.port, parse=False)
        parsedHeaders = headerToDict(header)
        self.assertTrue("Location" in parsedHeaders, parsedHeaders)
        self.assertEqual("/secure/login", parsedHeaders['Location'])

    def testLoginToSecureZone(self):
        header, body = getRequest(path='/secure', port=self.port, parse=False)
        parsedHeaders = headerToDict(header)
        self.assertEqual("/secure/login", parsedHeaders['Location'])

        header, body = getRequest(path='/secure/login', port=self.port, parse=False)
        parsedHeaders = headerToDict(header)
        Cookie = parsedHeaders['Set-Cookie']
        self.assertTrue("""<form method="POST" name="login" action="/login.action">""" in body, body)

        header, body = postRequest(path="/login.action", 
            port=self.port, parse=False, 
            data=urlencode(dict(username="admin", password="admin", formUrl="/login")),
            additionalHeaders=dict(Cookie=Cookie))
        
        header, body = getRequest(path='/secure/session', port=self.port, parse=False, additionalHeaders=dict(Cookie=Cookie))
        self.assertTrue("'user': <meresco.html.login.basichtmlloginform" in body, body)
