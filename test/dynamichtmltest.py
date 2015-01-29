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

from io import StringIO
import sys
from os import makedirs, rename
from os.path import join

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced

from weightless.core import compose, Yield, asString
from weightless.io import Reactor

from meresco.html import DynamicHtml
import collections


class DynamicHtmlTest(SeecrTestCase):

    def writeTemplate(self, name, contents):
        filename = join(self.tempdir, name) if name[0] != '/' else name
        with open(filename, "w") as fp:
            fp.write(contents)

    def testFileNotFound(self):
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEqual('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile "a" does not exist.', result)

    def testFileNotFound2(self):
        self.writeTemplate("a.sf", 'def main(pipe, **kwargs):\n yield pipe')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue(result.startswith('HTTP/1.0 404 Not Found'), result)
        self.assertTrue('File "path" does not exist.' in result, result)

    def testCustomFileNotFound(self):
        self.writeTemplate("redirect_to_me.sf", """
def main(**kwargs):
    yield "404 Handler"
""")
        d = DynamicHtml([self.tempdir], notFoundPage="/redirect_to_me", reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        headers, body = result.split('\r\n\r\n')
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8', headers)
        self.assertEqual('404 Handler', body)

    def testCustomFileNotFoundToFileThatDoesExist(self):
        d = DynamicHtml([self.tempdir], notFoundPage="/redirect_to_me", reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/a/path', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        headers, body = result.split('\r\n\r\n')
        self.assertEqual('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8', headers)
        self.assertEqual('File "redirect_to_me" does not exist.', body)

    def testASimpleFlatFile(self):
        self.writeTemplate('afile.sf', 'def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', result)

    def testPrefix(self):
        self.writeTemplate('afile.sf', 'def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'), prefix='/prefix')
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/prefix/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', result)

    def testSimpleGenerator(self):
        self.writeTemplate('testSimple.sf', """
def main(*args, **kwargs):
  for n in ('aap', 'noot', 'mies'):
    yield str(n)
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\naapnootmies', result)

    def testIncludeOther(self):
        self.writeTemplate('simple.sf', """
def main(*args, **kwargs):
    yield 'is'
    yield 'snake'
"""
        )
        self.writeTemplate('other.sf', """
import simple
def main(*args, **kwargs):
    yield 'me'
    yield simple.main()
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(compose(s.handleRequest(scheme='http', netloc='host.nl', path='/other', query='?query=something', fragments='#fragments', arguments={'query': 'something'})))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nmeissnake', result)

    def testUseModuleLocals(self):
        self.writeTemplate('testSimple.sf', """
moduleLocal = "local is available"
def main(*args, **kwargs):
    yield moduleLocal
"""
            )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('local is available' in result, result)

    def testUseModuleLocalsRecursive(self):
        self.writeTemplate('testSimple.sf', """
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
        self.writeTemplate('testSimple.sf', """
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
        with stderr_replaced() as err:
            self.writeTemplate('testSimple.sf', """
x = 1/0
def main(*args, **kwargs):
  pass
"""
            )
            s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
            result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))

            self.assertTrue('x = 1/0\nZeroDivisionError: division by zero' in result)

    def testRuntimeError(self):
        self.writeTemplate('testSimple.sf', """
def main(*args, **kwargs):
  yield 1/0
  yield "should not get here"
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest(scheme='http', netloc='host.nl', path='/testSimple', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue("HTTP/1.0 500 Internal Server Error\r\n\r\n" in result, result)
        self.assertTrue("ZeroDivisionError: division by zero" in result, result)

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

        self.writeTemplate('afile.sf', """#
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
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\ncallallany', ''.join(result))

        self.assertEqual([True], dos)
        self.assertEqual([True], onces)

    def testObservabilityOutsideMainOnModuleLevel(self):
        class X(object):
            def getX(*args, **kwargs):
                return "eks"

        self.writeTemplate('afile.sf', """#
x = observable.call.getX()
def main(*args, **kwargs):
  yield x
""")
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        d.addObserver(X())
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/afile', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\neks', ''.join(result))


    def testHeaders(self):
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate('file.sf', """
def main(Headers={}, *args, **kwargs):
    yield str(Headers)
""")
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file', query='?query=something', fragments='#fragments', arguments={'query': 'something'}, Headers={'key': 'value'})
        self.assertEqual("""HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{'key': 'value'}""", ''.join(result))


    def testCreateFileCausesReload(self):
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate('file1.sf', 'def main(*args, **kwargs): \n  yield "one"')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testModifyFileCausesReload(self):
        reactor = Reactor()

        self.writeTemplate('file1.sf', 'def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

        self.writeTemplate('file1.sf', 'def main(*args, **kwargs): \n  yield "two"')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\ntwo', ''.join(result))

    def testFileMovedIntoDirectoryCausesReload(self):
        reactor = Reactor()

        self.writeTemplate('/tmp/file1.sf', 'def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertEqual('HTTP/1.0 404 Not Found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile "file1" does not exist.', result)

        rename('/tmp/file1.sf', self.tempdir+'/file1.sf')
        reactor.step()

        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testReloadImportedModules(self):
        reactor = Reactor()

        self.writeTemplate('file1.sf', """
def main(value, *args, **kwargs):
    return "original template %s" % value
""")
        self.writeTemplate('file2.sf', """
import file1

def main(*args, **kwargs):
   yield file1.main(value='word!', *args, **kwargs)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file2'))
        self.assertTrue('original template word!' in result, result)

        self.writeTemplate('file1.sf', """
def main(value, *args, **kwargs):
    return "changed template %s" % value
""")

        reactor.step()
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file2'))
        self.assertTrue('changed template word!' in result, result)

    def testBuiltins(self):
        reactor = Reactor()

        self.writeTemplate('file1.sf', """
def main(headers={}, *args, **kwargs):
    yield str(True)
    yield str(False)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\nTrueFalse', ''.join(result))

        self.writeTemplate('file1.sf', """
def main(headers={}, *args, **kwargs):
    yield int('1')
    yield 2
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n12', ''.join(x for x in result))

        self.writeTemplate('file1.sf', """
def main(headers={}, *args, **kwargs):
    yield escapeHtml('&<>"')
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n&amp;&lt;&gt;&quot;', ''.join(result))

        self.writeTemplate('file1.sf', """
def main(headers={}, *args, **kwargs):
    yield str(list(zip([1,2,3],['one','two','three'])))
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        self.assertEqual('''HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n[(1, 'one'), (2, 'two'), (3, 'three')]''', ''.join(result))


    def testImportForeignModules(self):
        reactor = Reactor()

        self.writeTemplate('file1.sf', """
import sys

def main(headers={}, *args, **kwargs):
    yield str(sys)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor, allowedModules=['sys'])
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'})
        resultText = ''.join(result)
        self.assertTrue("<module 'sys' (built-in)>" in resultText, resultText)

        self.writeTemplate('file1.sf', """
import sys

def main(headers={}, *args, **kwargs):
    yield sys.__doc__
""")

        reactor.step()
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/file1', query='?query=something', fragments='#fragments', arguments={'query': 'something'}))
        self.assertTrue('This module provides access to some objects' in result, result)

    def testPipelining(self):
        self.writeTemplate('pipe1.sf', """
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        self.writeTemplate('pipe2.sf', """
def main(pipe=None, *args, **kwargs):
    yield 'two'
    yield 'three'
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/pipe1/pipe2')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEqual('onetwothreefour', message)

    def testLongPipeLine(self):
        filenames = []
        for i in range(10):
            filename = 'pipe%s' % i
            filenames.append(filename)
            self.writeTemplate(filename + '.sf', """
def main(pipe=None, *args, **kwargs):
    yield str(%s)
    for data in pipe:
        yield data
""" % i)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/' + '/'.join(filenames))
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEqual('0123456789', message)


    def testPipelineError(self):
        self.writeTemplate('pipe1.sf', """
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        self.writeTemplate('pipe2.sf', """
def main(pipe=None, *args, **kwargs):
    yield 'two'
    1/0
    yield 'three'

""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/pipe1/pipe2')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertTrue('division by zero' in message)

    def testYieldingEmptyPipe(self):
        self.writeTemplate('page.sf', """
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
        self.assertEqual('startend', message)

    def testPathTailDoesNotExist(self):
        self.writeTemplate('page.sf', """
def main(**kwargs):
    yield "nopipe"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest(scheme='http', netloc='host.nl', path='/page/doesnotexist')
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEqual('nopipe', message)

    def testIndexPage(self):
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = asString(d.handleRequest(path='/'))
        headers, message = result.split('\r\n\r\n')
        self.assertEqual('File "" does not exist.', message)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor, indexPage='/page')
        result = asString(d.handleRequest(path='/'))
        headers, message = result.split('\r\n\r\n')
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /page', headers)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor, indexPage='/page')
        result = asString(d.handleRequest(path='/', arguments={'a':['1']}))
        headers, message = result.split('\r\n\r\n')
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /page?a=1', headers)

    def testSFExtension(self):
        self.writeTemplate('page1.sf', """
def main(*args, **kwargs):
    yield "page1"
""")
        self.writeTemplate('page2.sf', """
import page1
def main(*args, **kwargs):
    yield page1.main()
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page2'))
        self.assertTrue('page1' in result, result)

    def testIgnoreNonSFExtensions(self):
        self.writeTemplate('page.otherextension.sf', """
def main(*args, **kwargs):
    yield "should not happen"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = asString(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        self.assertTrue('should not happen' not in result, result)

    def testHandlePOSTRequest(self):
        self.writeTemplate('page.sf', r"""
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
        self.writeTemplate('page.sf', r"""
def main(*args, **kwargs):
    yield http.redirect('/here')
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /here\r\n\r\n', result)

    def testRedirectWithAdditionalHeaders(self):
        self.writeTemplate('page.sf', r"""
def main(*args, **kwargs):
    yield http.redirect('/here', additionalHeaders={'Pragma': 'no-cache', 'Expires': '0'})
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest(scheme='http', netloc='host.nl', path='/page'))
        lines = result.strip().split("\r\n")
        self.assertEqual('HTTP/1.0 302 Found', lines[0])
        self.assertEqual(set(['Expires: 0', 'Location: /here', 'Pragma: no-cache']), set(lines[1:]))

    def testKeywordArgumentsArePassed(self):
        self.writeTemplate('afile.sf', 'def main(pipe, *args, **kwargs): \n  yield str(kwargs)')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/afile', netloc='localhost', key='value', key2='value2'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual({'Headers':{}, 'arguments':{}, 'path':'/afile', 'netloc':'localhost', 'key':'value', 'key2':'value2', 'scheme':'', 'query': ''}, eval(body))

    def createTwoPaths(self):
        path1 = join(self.tempdir, '1')
        path2 = join(self.tempdir, '2')
        makedirs(path1)
        makedirs(path2)
        return path1, path2

    def testMoreDirectories(self):
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path2, 'page.sf'), 'def main(*args,**kwargs):\n yield "page"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('page', body)

    def testImportFromFirstPath(self):
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path2, 'page.sf'), 'import one\ndef main(*args,**kwargs):\n yield one.main(*args,**kwargs)')
        self.writeTemplate(join(path1, 'one.sf'), 'def main(*args,**kwargs):\n yield "one"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)

    def testLoadTemplate(self):
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path2, 'page.sf'), """
def main(*args,**kwargs):
  one = importTemplate("one")
  yield one.main(*args,**kwargs)
""")
        self.writeTemplate(join(path1, 'one.sf'), """
def main(*args,**kwargs):
  yield "one"
""")
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)

    def testImportFromSecondPath(self):
        reactor = Reactor()
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path2, 'one.sf'), 'def main(*args,**kwargs):\n yield "one"')
        self.writeTemplate(join(path1, 'page.sf'), 'import one\ndef main(*args,**kwargs):\n yield one.main(*args,**kwargs)')
        d = DynamicHtml([path1, path2], reactor=reactor)
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)
        self.writeTemplate(join(path2, 'one.sf'), 'def main(*args,**kwargs):\n yield "two"')
        reactor.step()
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('two', body)

    def testFirstDirectoryHasTheRightFile(self):
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path1, 'page.sf'), 'def main(*args,**kwargs):\n yield "one"')
        self.writeTemplate(join(path2, 'page.sf'), 'def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([path1, path2], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)

    def testFirstDirectoryHasTheRightFileButSecondFileChanges(self):
        reactor = Reactor()
        path1, path2 = self.createTwoPaths()
        self.writeTemplate(join(path1, 'page.sf'), 'def main(*args,**kwargs):\n yield "one"')
        self.writeTemplate(join(path2, 'page.sf'), 'def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([path1, path2], reactor=reactor)
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)

        self.writeTemplate(join(path2, 'page.sf'), 'def main(*args,**kwargs):\n yield "three"')
        reactor.step()
        result = ''.join(d.handleRequest(path='/page'))
        header, body = result.split('\r\n\r\n')
        self.assertEqual('one', body)

    def testOldApiRaisesWarning(self):
        try:
            d = DynamicHtml("aDirectory", reactor=CallTrace('Reactor'))
            self.fail()
        except TypeError as te:
            self.assertEqual("Usage: DynamicHtml([aDirectory, ...], ....)", str(te))

    def testAdditionalGlobals(self):
        self.writeTemplate('afile.sf', 'def main(*args, **kwargs): \n  yield something')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'), additionalGlobals={'something':'YES'})
        head,body = ''.join(d.handleRequest(path='/afile')).split('\r\n\r\n')
        self.assertEqual('YES', body)

    def testChangingFileBeforeRetrievingFirstPage(self):
        reactor = Reactor()
        self.writeTemplate('one.sf', 'def main(*args,**kwargs):\n yield "one"')
        self.writeTemplate('two.sf', 'def main(*args,**kwargs):\n yield "two"')
        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate('one.sf', 'def main(*args,**kwargs):\n yield "one++"')
        reactor.step()
        header, body = ''.join(d.handleRequest(path='/two')).split('\r\n'*2)
        self.assertEqual('two', body)

    def testPassCallable(self):
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate('withcallable.sf', 
                "def main(*args, **kwargs):\n"
                "    def f():\n"
                "        pass\n"
                "    yield 'HTTP/1.0 200 OK\\r\\n\\r\\n'\n"
                "    yield f\n"
                "    yield 'text2'\n")
        reactor.step()
        r = list(d.handleRequest(path='/withcallable'))
        self.assertEqual("HTTP/1.0 200 OK\r\n\r\n", r[0])
        self.assertTrue(isinstance(r[1], collections.Callable))
        self.assertEqual("text2", r[2])

    def testPassYield(self):
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate("withyield.sf",
                "def main(*args, **kwargs):\n"
                "    yield 'HTTP/1.0 200 OK\\r\\n\\r\\n'\n"
                "    yield Yield\n"
                "    yield 'text2'\n")
        reactor.step()
        r = list(d.handleRequest(path='/withyield'))
        self.assertEqual("HTTP/1.0 200 OK\r\n\r\n", r[0])
        self.assertTrue(Yield is r[1], r[1])
        self.assertEqual("text2", r[2])

    def testPassCallableAsFirstThing(self):
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        self.writeTemplate("withcallable.sf", 
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
        self.assertTrue(isinstance(r[0], collections.Callable))
        self.assertTrue(isinstance(r[1], collections.Callable))
        self.assertEqual("HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n", r[2])
        self.assertEqual("this is no status line", r[3])
        self.assertTrue(isinstance(r[4], collections.Callable))
        self.assertEqual("text2", r[5])

    def testSetAttributeOnTemplateObjectNotAllowed(self):
        self.writeTemplate('two.sf', r"""

def main(*args, **kwargs):
    yield "Hoi"
""")
        self.writeTemplate('one.sf', r"""

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
        self.writeTemplate('one.sf', r"""
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
        self.writeTemplate('two.sf', r"""

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

        self.assertEqual(None, d.getModule('does-not-exist'))

        self.assertEqual('attr', one.attr)
        self.assertEqual('aye', one.sync())
        try:
            g = compose(one.asyncReturn())
            next(g)
        except StopIteration as e:
            self.assertEqual(('aye',), e.args)
        else:
            self.fail()

        self.assertEqual([], t1.calledMethodNames())
        self.assertEqual([], t2.calledMethodNames())
        list(compose(one.observableDownward()))
        self.assertEqual(['something'], t1.calledMethodNames())
        self.assertEqual(['something'], t2.calledMethodNames())
        self.assertEqual(('arg',), t1.calledMethods[0].args)
        self.assertEqual({'kw': 'kw'}, t1.calledMethods[0].kwargs)

        self.assertEqual(('one', ('two',), {'th': 'ree'}), two.parameterized('one', 'two', th='ree'))

        t1.calledMethods.reset()
        t2.calledMethods.reset()
        list(compose(two.main()))
        self.assertEqual(['something'], t1.calledMethodNames())
        self.assertEqual(['something'], t2.calledMethodNames())
        self.assertEqual(('arg',), t2.calledMethods[0].args)
        self.assertEqual({'kw': 'kw'}, t2.calledMethods[0].kwargs)

