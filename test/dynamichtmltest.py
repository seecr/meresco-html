from StringIO import StringIO
import sys
from cq2utils import CQ2TestCase
from cq2utils import CallTrace
from weightless import compose, Reactor

from os import makedirs, rename
from os.path import join

from dynamichtml import DynamicHtml

class DynamicHtmlTest(CQ2TestCase):

    def testFileNotFound(self):
        d = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        result = d.handleHttpRequest('http', 'host.nl', '/a/path', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile path does not exist.', ''.join(result))
        
    def testASimpleFlatFile(self):
        open(self.tempdir+'/afile','w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        result = d.handleHttpRequest('http', 'host.nl', '/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', ''.join(result))

    def testPrefix(self):
        open(self.tempdir+'/afile','w').write('def main(*args, **kwargs): \n  yield "John is a nut"')
        d = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'), prefix='/prefix')
        result = d.handleHttpRequest('http', 'host.nl', '/prefix/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nJohn is a nut', ''.join(result))

    def testSimpleGenerator(self):
        open(self.tempdir+'/testSimple', 'w').write(
"""
def main(*args, **kwargs):
  for n in ('aap', 'noot', 'mies'):
    yield str(n)
"""
        )
        s = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        result = ''.join(s.handleHttpRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\naapnootmies', result)

    def testIncludeOther(self):
        open(self.tempdir+'/simple', 'w').write(
"""
def main(*args, **kwargs):
    yield 'is'
    yield 'snake'
"""
        )
        open(self.tempdir+'/other', 'w').write(
"""
import simple
def main(*args, **kwargs):
    yield 'me'
    yield simple.main()
"""
        )
        s = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        result = ''.join(compose(s.handleHttpRequest('http', 'host.nl', '/other', '?query=something', '#fragments', {'query': 'something'})))
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nmeissnake', result)

    def testErrorWhileImporting(self):
        sys.stderr = StringIO()
        try:
            open(self.tempdir+'/testSimple', 'w').write(
"""
x = 1/0
def main(*args, **kwargs):
  pass
"""
            )
            s = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
            result = ''.join(s.handleHttpRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
            self.assertEquals('HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile testSimple does not exist.', result)
            self.assertTrue('x = 1/0\nZeroDivisionError: integer division or modulo by zero' in sys.stderr.getvalue())
        finally:
            sys.stderr = sys.__stderr__

    def testRuntimeError(self):
        open(self.tempdir+'/testSimple', 'w').write(
"""
def main(*args, **kwargs):
  yield 1/0
  input = yield
  next.send(bewerk(input))
  data = next.next()
  yield bewerk(data)
  yield any.process()
"""
        )
        s = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        result = ''.join(s.handleHttpRequest('http', 'host.nl', '/testSimple', '?query=something', '#fragments', {'query': 'something'}))
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nAn Error occured: "integer division or modulo by zero" at line 3 in /testSimple', result)


    def testObservability(self):
        class Something(object):
            def something(*args, **kwargs):
                return "something"
        
        open(self.tempdir+'/afile','w').write("""#
def main(*args, **kwargs):
  yield any.something()
  for i in all.something():
      yield i
  do.something()
""")
        d = DynamicHtml(self.tempdir, reactor=CallTrace('Reactor'))
        d.addObserver(Something())
        result = d.handleHttpRequest('http', 'host.nl', '/afile', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nsomethingsomething', ''.join(result))


    def testHeaders(self):
        from weightless import Reactor
        reactor = Reactor()
        
        d = DynamicHtml(self.tempdir, reactor=reactor)
        open(self.tempdir+'/file','w').write('def main(headers={}, *args, **kwargs): \n  yield str(headers)')
        reactor.step()
        
        result = d.handleHttpRequest('http', 'host.nl', '/file', '?query=something', '#fragments', {'query': 'something'}, headers={'key': 'value'})
        self.assertEquals("""HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{'key': 'value'}""", ''.join(result))
        

    def testCreateFileCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()
        
        d = DynamicHtml(self.tempdir, reactor=reactor)
        open(self.tempdir+'/file1','w').write('def main(*args, **kwargs): \n  yield "one"')
        reactor.step()
        
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testModifyFileCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()
        
        open(self.tempdir+'/file1','w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml(self.tempdir, reactor=reactor)
        
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

        open(self.tempdir+'/file1','w').write('def main(*args, **kwargs): \n  yield "two"')
        reactor.step()
        
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\ntwo', ''.join(result))

    def testFileMovedIntoDirectoryCausesReload(self):
        from weightless import Reactor
        reactor = Reactor()
        
        open('/tmp/file1','w').write('def main(*args, **kwargs): \n  yield "one"')
        d = DynamicHtml(self.tempdir, reactor=reactor)
        
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\nFile file1 does not exist.', ''.join(result))

        rename('/tmp/file1', self.tempdir+'/file1')
        reactor.step()

        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\none', ''.join(result))

    def testReloadImportedModules(self):
        from weightless import Reactor
        reactor = Reactor()
        
        open(self.tempdir + '/file1','w').write("""
def main(value, headers={}, *args, **kwargs):
    return value
""")
        open(self.tempdir + '/file2','w').write("""
import file1

def main(headers={}, *args, **kwargs):
   yield file1.main(value='word!', headers=headers, *args, **kwargs)
""")

        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/file2', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nword!', ''.join(result))

        open(self.tempdir + '/file1','w').write("""
def main(value, headers={}, *args, **kwargs):
    return "the value is: "+ value
""")

        reactor.step()
        result = d.handleHttpRequest('http', 'host.nl', '/file2', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nthe value is: word!', ''.join(result))

        
    def testBuiltins(self):
        from weightless import Reactor
        reactor = Reactor()
        
        open(self.tempdir + '/file1','w').write("""
def main(headers={}, *args, **kwargs):
    yield str(True)
    yield str(False)
""")

        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\nTrueFalse', ''.join(result))

        open(self.tempdir + '/file1','w').write("""
def main(headers={}, *args, **kwargs):
    yield int('1')
""")

        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n1', ''.join(str(x) for x in result))

        open(self.tempdir + '/file1','w').write("""
def main(headers={}, *args, **kwargs):
    yield escapeHtml('&<>')
""")

        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n&amp;&lt;&gt;', ''.join(result))
        

    def testImportForgeinModules(self):
        reactor = Reactor()
        
        open(self.tempdir + '/file1','w').write("""
import Ft

def main(headers={}, *args, **kwargs):
    yield str(Ft)
""")

        d = DynamicHtml(self.tempdir, reactor=reactor, allowedModules=['Ft'])
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals("HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n<module 'Ft' from '/usr/lib/python2.5/site-packages/Ft/__init__.pyc'>", ''.join(result))

        open(self.tempdir + '/file1','w').write("""
import Ft

def main(headers={}, *args, **kwargs):
    yield Ft.__doc__
""")

        reactor.step()
        result = d.handleHttpRequest('http', 'host.nl', '/file1', '?query=something', '#fragments', {'query': 'something'})
        self.assertEquals('HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\n\r\n\n4Suite: an open-source platform for XML and RDF processing.\n\nCopyright 2004 Fourthought, Inc. (USA).\nDetailed license and copyright information: http://4suite.org/COPYRIGHT\nProject home, documentation, distributions: http://4suite.org/\n', ''.join(result))

    def testPipelining(self):
        open(self.tempdir + '/pipe1','w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        open(self.tempdir + '/pipe2','w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'two'
    yield 'three'
""")
        reactor = Reactor()
        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/pipe1/pipe2', '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('onetwothreefour', message)

    def testLongPipeLine(self):
        filenames = []
        for i in range(10):
            filename = 'pipe%s' % i
            filenames.append(filename)
            open(self.tempdir + '/' + filename, 'w').write("""
def main(pipe=None, *args, **kwargs):
    yield str(%s)
    for data in pipe:
        yield data
""" % i)
        
        reactor = Reactor()
        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/' + '/'.join(filenames), '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('0123456789', message)


    def testPipelineError(self):
        open(self.tempdir + '/pipe1','w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'one'
    for data in pipe:
        yield data
    yield 'four'
""")
        open(self.tempdir + '/pipe2','w').write("""
def main(pipe=None, *args, **kwargs):
    yield 'two'
    1/0
    yield 'three'
    
""")
        reactor = Reactor()
        d = DynamicHtml(self.tempdir, reactor=reactor)
        result = d.handleHttpRequest('http', 'host.nl', '/pipe1/pipe2', '', '', {})
        headers, message = ''.join(result).split('\r\n\r\n')
        self.assertEquals('onetwoAn Error occured: "integer division or modulo by zero" at line 4 in /pipe1', message)