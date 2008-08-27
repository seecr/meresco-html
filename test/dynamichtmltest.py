from StringIO import StringIO
import sys
from cq2utils import CQ2TestCase
from cq2utils import CallTrace, MATCHALL
from weightless import compose, Reactor

from os import makedirs, rename
from os.path import join

from dynamichtml import DynamicHtml

class DynamicHtmlTest(CQ2TestCase):

    def testFileNotFound(self):
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = d.handleRequest('http', 'host.nl', '/a/path', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile path does not exist.', ''.join(result))

    def testASimpleFlatFile(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = d.handleRequest('http', 'host.nl', '/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', ''.join(result))

    def testPrefix(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'), prefix='/prefix')
        result = d.handleRequest('http', 'host.nl', '/prefix/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', ''.join(result))

    def testSimpleGenerator(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def main(*args, **kwargs):
  for n in ('aap', 'noot', 'mies'):
    yield str(n)
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\naapnootmies', result)

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
        result = ''.join(compose(s.handleRequest('http', 'host.nl', '/other', '?query=something', '#fragments', {'query': 'something'})))
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nmeissnake', result)


    def testUseModuleLocals(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
moduleLocal = "local is available"
def main(*args, **kwargs):
    yield moduleLocal
"""
            )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
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
        result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
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
        result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
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
            result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
            self.assertTrue('x = 1/0\nZeroDivisionError: integer division or modulo by zero' in result)
        finally:
            sys.stderr = sys.__stderr__

    def testRuntimeError(self):
        open(self.tempdir+'/testSimple.sf', 'w').write("""
def main(*args, **kwargs):
  yield 1/0
  input = yield
  next.send(bewerk(input))
  data = next.next()
  yield bewerk(data)
  yield any.process()
"""
        )
        s = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(s.handleRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
        self.assertTrue("HTTP/1.0 500 Internal Server Error\r\n\r\n" in result, result)
        self.assertTrue("integer division or modulo by zero" in result, result)


    def testObservability(self):
        class Something(object):
            def something(*args, **kwargs):
                return "something"

        open(self.tempdir+'/afile.sf', 'w').write("""#
def main(*args, **kwargs):
  yield any.something()
  for i in all.something():
      yield i
  do.something()
""")
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        d.addObserver(Something())
        result = d.handleRequest('http', 'host.nl', '/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nsomethingsomething', ''.join(result))

    def testObservabilityOutsideMainOnModuleLevel(self):
        class X(object):
            def getX(*args, **kwargs):
                return "eks"

        open(self.tempdir+'/afile.sf', 'w').write("""#
x = any.getX()
def main(*args, **kwargs):
  yield x
""")
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        d.addObserver(X())
        result = d.handleRequest('http', 'host.nl', '/afile', '', '', {})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\neks', ''.join(result))


    def testHeaders(self):
        from weightless import Reactor
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(self.tempdir+'/file.sf', 'w').write("""
def main(Headers={}, *args, **kwargs):
    yield str(Headers)
""")
        reactor.step()

        result = d.handleRequest('http', 'host.nl', '/file', '?query=something', '#fragments', arguments={'query': 'something'}, Headers={'key': 'value'})
        self.assertEquals("""HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{'key': 'value'}""", ''.join(result))


    def testCreateFileCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()

        d = DynamicHtml([self.tempdir], reactor=reactor)
        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        reactor.step()

        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testModifyFileCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()

        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

        open(self.tempdir+'/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "two"')
        reactor.step()

        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\ntwo', ''.join(result))

    def testFileMovedIntoDirectoryCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()

        open('/tmp/file1.sf', 'w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml([self.tempdir], reactor=reactor)

        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile file1 does not exist.', ''.join(result))

        rename('/tmp/file1.sf', self.tempdir+'/file1.sf')
        reactor.step()

        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testReloadImportedModules(self):
        from weightless import Reactor
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
        result = ''.join(d.handleRequest('http', 'host.nl', '/file2'))
        self.assertTrue('original template word!' in result, result)

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(value, *args, **kwargs):
    return "changed template %s" % value
""")

        reactor.step()
        result = ''.join(d.handleRequest('http', 'host.nl', '/file2'))
        self.assertTrue('changed template word!' in result, result)

    def testBuiltins(self):
        from weightless import Reactor
        reactor = Reactor()

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield str(True)
    yield str(False)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nTrueFalse', ''.join(result))

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield int('1')
    yield 2
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n12', ''.join(x for x in result))

        open(self.tempdir + '/file1.sf', 'w').write("""
def main(headers={}, *args, **kwargs):
    yield escapeHtml('&<>"')
""")

        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n&amp;&lt;&gt;&quot;', ''.join(result))


    def testImportForeignModules(self):
        reactor = Reactor()

        open(self.tempdir + '/file1.sf', 'w').write("""
import Ft

def main(headers={}, *args, **kwargs):
    yield str(Ft)
""")

        d = DynamicHtml([self.tempdir], reactor=reactor, allowedModules=['Ft'])
        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        resultText = ''.join(result)
        self.assertTrue(resultText.endswith("/Ft/__init__.pyc'>"), resultText)

        open(self.tempdir + '/file1.sf', 'w').write("""
import Ft

def main(headers={}, *args, **kwargs):
    yield Ft.__doc__
""")

        reactor.step()
        result = d.handleRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n\n4Suite: an open-source platform for XML and RDF processing.\n\nCopyright 2004 Fourthought, Inc. (USA).\nDetailed license and copyright information: http://4suite.org/COPYRIGHT\nProject home, documentation, distributions: http://4suite.org/\n', ''.join(result))

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
        result = d.handleRequest('http', 'host.nl', '/pipe1/pipe2', '', '', {})
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
        result = d.handleRequest('http', 'host.nl', '/' + '/'.join(filenames), '', '', {})
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
        result = d.handleRequest('http', 'host.nl', '/pipe1/pipe2', '', '', {})
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
        result = d.handleRequest('http', 'host.nl', '/page', '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('startend', message)

    def testIndexPage(self):
        open(self.tempdir + '/page.sf', 'w').write("""
def main(*args, **kwargs):
    yield "index"

""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = d.handleRequest('http', 'host.nl', '/', '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('File  does not exist.', message)

        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor, indexPage='/page')
        result = d.handleRequest('http', 'host.nl', '/', '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('index', message)

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
        result = ''.join(d.handleRequest('http', 'host.nl', '/page2', '', '', {}))
        self.assertTrue('page1' in result, result)

    def testIgnoreNonSFExtensions(self):
        open(self.tempdir + '/page.otherextension.sf', 'w').write("""
def main(*args, **kwargs):
    yield "should not happen"
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest('http', 'host.nl', '/page', '', '', {}))
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
        result = ''.join(d.handleRequest('http', 'host.nl', '/page', '', '', arguments={}, RequestURI= 'http://host.nl/page' , Method='POST', Body='label=value&otherlabel=value', Headers={'Content-Type':'application/x-www-form-urlencoded'}))

        self.assertTrue('Content-Type: application/x-www-form-urlencoded\nBody: label=value&otherlabel=value\nMethod: POST\n' in result, result)

    def testRedirect(self):
        open(self.tempdir + '/page.sf', 'w').write(r"""
def main(*args, **kwargs):
    yield http.redirect('/here')
""")
        reactor = Reactor()
        d = DynamicHtml([self.tempdir], reactor=reactor)
        result = ''.join(d.handleRequest('http', 'host.nl', '/page', '', '', {}))
        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: /here\r\n\r\n', result)

    def testKeywordArgumentsArePassed(self):
        open(self.tempdir+'/afile.sf', 'w').write('def main(pipe, *args, **kwargs): \n  yield str(kwargs)')
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        result = ''.join(d.handleRequest(path='/afile', netloc='localhost', key='value', key2='value2'))
        header, body = result.split('\r\n\r\n')
        self.assertEquals({'Headers':MATCHALL, 'arguments':MATCHALL, 'path':'/afile', 'netloc':'localhost', 'key':'value', 'key2':'value2', 'scheme':'', 'query': ''}, eval(body))

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
        
    def testImportFromSecondPath(self):
        from weightless import Reactor
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
        from weightless import Reactor
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
