from seecr.test import SeecrTestCase
from seecr.utils.generatorutils import asString

from seecr.html import PostActions

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



