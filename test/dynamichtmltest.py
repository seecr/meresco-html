# -*- coding: utf-8 -*-
## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2014 Seecr (Seek You Too B.V.) http://seecr.nl
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

from StringIO import StringIO
import sys
from os import makedirs, rename
from os.path import join

from seecr.test import SeecrTestCase, CallTrace

from weightless.core import compose, Yield, asString
from weightless.io import Reactor

from meresco.html import DynamicHtml


class DynamicHtmlTest(SeecrTestCase):
    def testFileNotFound(self):
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEquals('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile "a" does not exist.', result)

    def testFileNotFound2(self):
        with open(join(self.tempdir, 'a.sf'), 'w') as f:
            f.write('def main(pipe, **kwargs):\n yield pipe')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue(result.startswith('HTTP/1.0 404 Not Found'), result)
        self.assertTrue('File "path" does not exist.' in result, result)

    def testCustomFileNotFound(self):
        open(join(self.tempdir, "redirect_to_me.sf"), 'w').write("""
def main(**kwargs):
    yield "404 Handler"
""")
        d = DynamicHtml([self.tempdir], notFoundPage="/redirect_to_me", reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        headers, body = result.split('\r\n\r\n')
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8', headers)
        self.assertEquals('404 Handler', body)

    def testCustomFileNotFoundToFileThatDoesExist(self):
        d = DynamicHtml([self.tempdir], notFoundPage="/redirect_to_me", reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        headers, body = result.split('\r\n\r\n')
        self.assertEquals('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8', headers)
        self.assertEquals('File "redirect_to_me" does not exist.', body)

    def testASimpleFlatFile(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', result)

    def testPrefix(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'), prefix='/prefix')
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/prefix/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', result)

    def testSimpleGenerator(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def main(*args, **kwargs):
  for n in ('aap', 'noot', 'mies'):
    yield str(n)
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\naapnootmies', result)

    def testIncludeOther(self):
        open(self.tempdir+'/simple.sf', 'w').write("""
def main(*args, **kwargs):
    yield 'is'
    yield 'snake'
"""
        )
        open(self.tempdir+'/other.sf', 'w').write("""
import simple
def main(*args, **kwargs):
    yield 'me'
    yield simple.main()
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(compose(s.handleRequest(scheme='http', netloc='host.nl', path='/other', query='?query=something', fragments='#fragments', arguments={'query': 'something'})))
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nmeissnake', result)

    def testUseModuleLocals(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
moduleLocal = "local is available"
def main(*args, **kwargs):
    yield moduleLocal
"""
            )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('local is available' in result, result)

    def testUseModuleLocalsRecursive(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def recursiveModuleLocal(recurse):
    if recurse:
        return recursiveModuleLocal(recurse=False)
    return "recursiveModuleLocal result"

def main(*args, **kwargs):
    yield recursiveModuleLocal(recurse=True)
"""
            )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('recursiveModuleLocal result' in result, result)

    def testUseModuleLocalsCrissCross(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def f():
    return "f()"

def g():
    return "g(%s)" % f()

def main(*args, **kwargs):
    yield g()
"""
            )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('g(f())' in result, result)

    def testErrorWhileImporting(self):
        sys.stderr = StringIO()
        try:
            open(self.tempdir+'/testSimple.sf', 'w').write("""
x = 1/0
def main(*args, **kwargs):
  pass
"""
            )
            s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
            result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))

            self.assertTrue('x = 1/0\nZeroDivisionError: integer division or modulo by zero' in result)
        finally:
            sys.stderr = sys.__stderr__

    def testRuntimeError(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def main(*args, **kwargs):
  yield 1/0
  yield "should not get here"
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue("HTTP/1.0 500 Internal Server Error\r\n\r\n" in result, result)
        self.assertTrue("integer division or modulo by zero" in result, result)

    def testObservability(self):
        onces = []
        dos = []
        class Something(object):
            def callSomething(self, *args, **kwargs):
                return "call"
            def allSomething(self, *args, **kwargs):
                yield "all"
            def anySomething(self, *args, **kwargs):
                yield "any"
                raise StopIteration('retval')
            def doSomething(self, *args, **kwargs):
                dos.append(True)
            def onceSomething(self, *args, **kwargs):
                onces.append(True)

        open(self.tempdir+'/afile.sf', 'w').write("""#
def main(*args, **kwargs):
  result = observable.call.callSomething()
  yield result
  yield observable.all.allSomething()
  result = yield observable.any.anySomething()
  assert result == 'retval'
  observable.do.doSomething()
  yield observable.once.onceSomething()
""")
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        d.addObserver(Something())
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\ncallallany', ''.join(result))

        self.assertEquals([True], dos)
        self.assertEquals([True], onces)

    def testObservabilityOutsideMainOnModuleLevel(self):
        class X(object):
            def getX(*args, **kwargs):
                return "eks"

        open(self.tempdir+'/afile.sf', 'w').write("""#
x = observable.call.getX()
def main(*args, **kwargs):
  yield x
""")
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        d.addObserver(X())
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\neks', ''.join(result))


    def testHeaders(self):
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(self.tempdir+'/file.sf', 'w').write("""
def main(Headers={}, *args, **kwargs):
    yield str(Headers)
""")
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file', query='?query=something', fragments='#fragments', arguments={'query': 'something'}, Headers={'key': 'value'})
        self.assertEquals("""HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{'key': 'value'}""", ''.join(result))


    def testCreateFileCausesReload(self):
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testModifyFileCausesReload(self):
        reactor = Reactor()

        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "two"')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\ntwo', ''.join(result))

    def testFileMovedIntoDirectoryCausesReload(self):
        reactor = Reactor()

        open('/tmp/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEquals('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile "file1" does not exist.', result)

        rename('/tmp/file1.sf', self.tempdir+'/file1.sf')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testReloadImportedModules(self):
        reactor = Reactor()

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(value, *args, **kwargs):
    return "original template %s" % value
""")
        open(self.tempdir + '/file2.sf', 'w').write("""
import file1

def main(*args, **kwargs):
   yield file1.main(value='word!', *args, **kwargs)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file2'))
        self.assertTrue('original template word!' in result, result)

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(value, *args, **kwargs):
    return "changed template %s" % value
""")

        reactor.step()
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file2'))
        self.assertTrue('changed template word!' in result, result)

    def testBuiltins(self):
        reactor = Reactor()

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield str(True)
    yield str(False)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nTrueFalse', ''.join(result))

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield int('1')
    yield 2
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n12', ''.join(x for x in result))

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield escapeHtml('&<>"')
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n&amp;&lt;&gt;&quot;', ''.join(result))

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield str(zip([1,2,3],['one','two','three']))
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEquals('''HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n[(1, 'one'), (2, 'two'), (3, 'three')]''', ''.join(result))


    def testImportForeignModules(self):
        reactor = Reactor()

        open(self.tempdir + '/file1.sf', 'w').write("""
import sys

def main(headers={}, *args, **kwargs):
    yield str(sys)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor, allowedModules=['sys'])
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        resultText = ''.join(result)
        self.assertTrue("<module 'sys' (built-in)>" in resultText, resultText)

        open(self.tempdir + '/file1.sf', 'w').write("""
import sys

def main(headers={}, *args, **kwargs):
    yield sys.__doc__
""")

        reactor.step()
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('This module provides access to some objects' in result, result)

    def testPipelining(self):
        open(self.tempdir + '/pipe1.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        open(self.tempdir + '/pipe2.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'two'
    yield 'three'
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/pipe1/pipe2')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('onetwothreefour', message)

    def testLongPipeLine(self):
        filenames = []
        for i in range(10):
            filename = 'pipe%s' % i
            filenames.append(filename)
            open(self.tempdir + '/' + filename + '.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield str(%s)
    for data in pipe:
        yield data
""" % i)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/' + '/'.join(filenames))
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('0123456789', message)


    def testPipelineError(self):
        open(self.tempdir + '/pipe1.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        open(self.tempdir + '/pipe2.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'two'
    1/0
    yield 'three'

""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/pipe1/pipe2')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertTrue('integer division or modulo by zero' in message)

    def testYieldingEmptyPipe(self):
        open(self.tempdir + '/page.sf', 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield "start"
    for data in pipe:
        yield data
    yield 'end'

""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/page')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('startend', message)

    def testPathTailDoesNotExist(self):
        open(self.tempdir + '/page.sf', 'w').write("""
def main(**kwargs):
    yield "nopipe"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/page/doesnotexist')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('nopipe', message)

    def testIndexPage(self):
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = asString(d.handleRequest(path='/'))
        headers, message = result.split('\r\n\r\n')
        self.assertEquals('File "" does not exist.', message)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor, indexPage='/page')
        result = asString(d.handleRequest(path='/'))
        headers, message = result.split('\r\n\r\n')
        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: /page', headers)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor, indexPage='/page')
        result = asString(d.handleRequest(path='/', arguments={'a':['1']}))
        headers, message = result.split('\r\n\r\n')
        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: /page?a=1', headers)

    def testSFExtension(self):
        open(self.tempdir + '/page1.sf', 'w').write("""
def main(*args, **kwargs):
    yield "page1"
""")
        open(self.tempdir + '/page2.sf', 'w').write("""
import page1
def main(*args, **kwargs):
    yield page1.main()
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page2'))
        self.assertTrue('page1' in result, result)

    def testIgnoreNonSFExtensions(self):
        open(self.tempdir + '/page.otherextension.sf', 'w').write("""
def main(*args, **kwargs):
    yield "should not happen"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        self.assertTrue('should not happen' not in result, result)

    def testHandlePOSTRequest(self):
        open(self.tempdir + '/page.sf', 'w').write(r"""
def main(Headers={}, Body=None, Method=None, *args, **kwargs):
    yield 'Content-Type: %s\n' % Headers.get('Content-Type')
    yield 'Body: %s\n' % Body
    yield 'Method: %s\n' % Method
"""
        )
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page', arguments={}, RequestURI='http://host.nl/page', Method='POST', Body='label=value&otherlabel=value', Headers={'Content-Type':'application/x-www-form-urlencoded'}))

        self.assertTrue('Content-Type: application/x-www-form-urlencoded\nBody: label=value&otherlabel=value\nMethod: POST\n' in result, result)

    def testRedirect(self):
        open(self.tempdir + '/page.sf', 'w').write(r"""
def main(*args, **kwargs):
    yield http.redirect('/here')
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: /here\r\n\r\n', result)

    def testRedirectWithAdditionalHeaders(self):
        open(self.tempdir + '/page.sf', 'w').write(r"""
def main(*args, **kwargs):
    yield http.redirect('/here', additionalHeaders={'Pragma': 'no-cache', 'Expires': '0'})
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        self.assertEquals('HTTP/1.0 302 Found\r\nExpires: 0\r\nLocation: /here\r\nPragma: no-cache\r\n\r\n', result)

    def testKeywordArgumentsArePassed(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(pipe, *args, **kwargs): \n  yield str(kwargs)')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/afile', netloc='localhost', key='value', key2='value2'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals({'Headers':{}, 'arguments':{}, 'path':'/afile', 'netloc':'localhost', 'key':'value', 'key2':'value2', 'scheme':'', 'query': ''}, eval(body))

    def createTwoPaths(self):
        path1 = join(self.tempdir, '1')
        path2 = join(self.tempdir, '2')
        makedirs(path1)
        makedirs(path2)
        return path1, path2

    def testMoreDirectories(self):
        path1, path2 = self.createTwoPaths()
        open(join(path2, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "page"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('page', body)

    def testImportFromFirstPath(self):
        path1, path2 = self.createTwoPaths()
        open(join(path2, 'page.sf'), 'w').write('import one\ndef main(*args,**kwargs):\n yield one.main(*args,**kwargs)')
        open(join(path1, 'one.sf'), 'w').write('def main(*args,**kwargs):\n yield "one"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)

    def testLoadTemplate(self):
        path1, path2 = self.createTwoPaths()
        open(join(path2, 'page.sf'), 'w').write("""
def main(*args,**kwargs):
  one = importTemplate("one")
  yield one.main(*args,**kwargs)
""")
        open(join(path1, 'one.sf'), 'w').write("""
def main(*args,**kwargs):
  yield "one"
""")
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)

    def testImportFromSecondPath(self):
        reactor = Reactor()
        path1, path2 = self.createTwoPaths()
        open(join(path2, 'one.sf'), 'w').write('def main(*args,**kwargs):\n yield "one"')
        open(join(path1, 'page.sf'), 'w').write('import one\ndef main(*args,**kwargs):\n yield one.main(*args,**kwargs)')
        d = DynamicHtml([path1, path2], reactor=reactor)
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)
        open(join(path2, 'one.sf'), 'w').write('def main(*args,**kwargs):\n yield "two"')
        reactor.step()
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('two', body)

    def testFirstDirectoryHasTheRightFile(self):
        path1, path2 = self.createTwoPaths()
        open(join(path1, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "one"')
        open(join(path2, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)

    def testFirstDirectoryHasTheRightFileButSecondFileChanges(self):
        reactor = Reactor()
        path1, path2 = self.createTwoPaths()
        open(join(path1, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "one"')
        open(join(path2, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([path1, path2], reactor=reactor)
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)

        open(join(path2, 'page.sf'), 'w').write('def main(*args,**kwargs):\n yield "three"')
        reactor.step()
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals('one', body)

    def testOldApiRaisesWarning(self):
        try:
            d = DynamicHtml("aDirectory", reactor=CallTrace('Reactor'))
            self.fail()
        except TypeError, te:
            self.assertEquals("Usage: DynamicHtml([aDirectory, ...], ....)", str(te))

    def testAdditionalGlobals(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(*args, **kwargs): \n  yield something')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'), additionalGlobals={'something':'YES'})
        head,body = ''.join(d.handleRequest(path='/afile')).split('\r\n\r\n')
        self.assertEquals('YES', body)

    def testChangingFileBeforeRetrievingFirstPage(self):
        reactor = Reactor()
        open(join(self.tempdir, 'one.sf'), 'w').write('def main(*args,**kwargs):\n yield "one"')
        open(join(self.tempdir, 'two.sf'), 'w').write('def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(join(self.tempdir, 'one.sf'), 'w').write('def main(*args,**kwargs):\n yield "one++"')
        reactor.step()
        header, body = ''.join(d.handleRequest(path='/two')).split('\r\n'*2)
        self.assertEquals('two', body)

    def testPassCallable(self):
        reactor = Reactor()
        tmplatename = join(self.tempdir, 'withcallable.sf')
        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(tmplatename, 'w').write(
                "def main(*args, **kwargs):\n"
                "    def f():\n"
                "        pass\n"
                "    yield 'HTTP/1.0 200 OK\\r\\n\\r\\n'\n"
                "    yield f\n"
                "    yield 'text2'\n")
        reactor.step()
        r = list(d.handleRequest(path='/withcallable'))
        self.assertEquals("HTTP/1.0 200 OK\r\n\r\n", r[0])
        self.assertTrue(callable(r[1]))
        self.assertEquals("text2", r[2])

    def testPassYield(self):
        reactor = Reactor()
        tmplatename = join(self.tempdir, 'withyield.sf')
        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(tmplatename, 'w').write(
                "def main(*args, **kwargs):\n"
                "    yield 'HTTP/1.0 200 OK\\r\\n\\r\\n'\n"
                "    yield Yield\n"
                "    yield 'text2'\n")
        reactor.step()
        r = list(d.handleRequest(path='/withyield'))
        self.assertEquals("HTTP/1.0 200 OK\r\n\r\n", r[0])
        self.assertTrue(Yield is r[1], r[1])
        self.assertEquals("text2", r[2])

    def testPassCallableAsFirstThing(self):
        reactor = Reactor()
        tmplatename = join(self.tempdir, 'withcallable.sf')
        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(tmplatename, 'w').write(
                "def main(*args, **kwargs):\n"
                "    def f():\n"
                "        pass\n"
                "    yield f\n"
                "    yield f\n"
                "    yield 'this is no status line'\n"
                "    yield f\n"
                "    yield 'text2'\n")
        reactor.step()
        r = list(d.handleRequest(path='/withcallable'))
        self.assertTrue(callable(r[0]))
        self.assertTrue(callable(r[1]))
        self.assertEquals("HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n", r[2])
        self.assertEquals("this is no status line", r[3])
        self.assertTrue(callable(r[4]))
        self.assertEquals("text2", r[5])

    def testSetAttributeOnTemplateObjectNotAllowed(self):
        open(self.tempdir + '/two.sf', 'w').write(r"""

def main(*args, **kwargs):
    yield "Hoi"
""")
        open(self.tempdir + '/one.sf', 'w').write(r"""

import two
two.three = 3

def main(*args, **kwargs):
    yield "Hoi"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result =  ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/one', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('AttributeError' in result, result)

    def testShouldExposeLoadedModulesForTestingPurposes(self):
        open(self.tempdir + '/one.sf', 'w').write(r"""
attr = 'attr'
def sync():
    return 'aye'
def asyncReturn():
    raise StopIteration('aye')
    yield
def observableDownward():
    yield observable.all.something('arg', kw='kw')
def main(*args, **kwargs):
    yield "Hoi"
""")
        open(self.tempdir + '/two.sf', 'w').write(r"""

import one

def parameterized(arg, *args, **kwargs):
    return arg, args, kwargs

def main(*args, **kwargs):
    yield one.observableDownward()
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        t1 = CallTrace('t1')
        t2 = CallTrace('t2')
        d.addObserver(t1)
        d.addObserver(t2)
        one = d.getModule(name='one')
        two = d.getModule('two')

        self.assertEquals(None, d.getModule('does-not-exist'))

        self.assertEquals('attr', one.attr)
        self.assertEquals('aye', one.sync())
        try:
            g = compose(one.asyncReturn())
            g.next()
        except StopIteration, e:
            self.assertEquals(('aye',), e.args)
        else:
            self.fail()

        self.assertEquals([], t1.calledMethodNames())
        self.assertEquals([], t2.calledMethodNames())
        list(compose(one.observableDownward()))
        self.assertEquals(['something'], t1.calledMethodNames())
        self.assertEquals(['something'], t2.calledMethodNames())
        self.assertEquals(('arg',), t1.calledMethods[0].args)
        self.assertEquals({'kw': 'kw'}, t1.calledMethods[0].kwargs)

        self.assertEquals(('one', ('two',), {'th': 'ree'}), two.parameterized('one', 'two', th='ree'))

        t1.calledMethods.reset()
        t2.calledMethods.reset()
        list(compose(two.main()))
        self.assertEquals(['something'], t1.calledMethodNames())
        self.assertEquals(['something'], t2.calledMethodNames())
        self.assertEquals(('arg',), t2.calledMethods[0].args)
        self.assertEquals({'kw': 'kw'}, t2.calledMethods[0].kwargs)

