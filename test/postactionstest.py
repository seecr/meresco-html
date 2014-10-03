## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.html import PostActions
from weightless.core import asString

class PostActionsTest(SeecrTestCase):

    def testMethodsAllowed(self):
        p = PostActions()

        response = asString(p.handleRequest(Method="GET", path="/"))
        self.assertEquals('HTTP/1.0 405 Method Not Allowed\r\nContent-Type: text/html; charset=utf-8\r\nAllow: POST\r\n\r\n<h1>Method Not Allowed</h1>', response)
        response = asString(p.handleRequest(Method="Get", path="/"))
        self.assertEquals('HTTP/1.0 405 Method Not Allowed\r\nContent-Type: text/html; charset=utf-8\r\nAllow: POST\r\n\r\n<h1>Method Not Allowed</h1>', response)

    def testNoContent(self):
        p = PostActions()

        response = asString(p.handleRequest(Method="POST", path="/"))
        self.assertEquals('HTTP/1.0 204 No Content\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nNo Content', response)


        def default(**kwargs):
            yield "This is the default action"

        p.defaultAction(default)
        response = asString(p.handleRequest(Method="POST", path="/"))
        self.assertEquals("This is the default action", response)


    def testRegisterAction(self):
        p = PostActions()
        def myAction(**kwargs):
            yield "My Action is done"

        p.registerAction("act", myAction)
        response = asString(p.handleRequest(Method="POST", path="/act"))
        self.assertEquals("My Action is done", response)



