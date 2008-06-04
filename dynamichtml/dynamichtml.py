from glob import glob
from os.path import join, isfile, isdir, dirname, basename, abspath
from os import walk as dirwalk
from sys import exc_info
from traceback import print_exc, format_exc
from cgi import parse_qs
from urlparse import urlsplit

from pyinotify import WatchManager, Notifier, EventsCodes, ProcessEvent

from cgi import escape as escapeHtml
from xml.sax.saxutils import escape as escapeXml
from amara.binderytools import bind_stream
from time import time
from urllib import urlencode
from math import ceil

from meresco.framework import Observable, decorate, compose
from cq2utils.wrappers import wrapp

class EmptyModule:
    pass

class DirectoryWatcher(object):
    def __init__(self, path, mask, method):
        self._wm = WatchManager()
        self._wm.add_watch(path, mask)
        self._notifier = Notifier(self._wm, method)

    def fileno(self):
        return self._notifier._fd

    def close(self):
        self._notifier.stop()

    def __call__(self):
        self._notifier.read_events()
        self._notifier.process_events()

class DynamicHtmlException(Exception):
    pass

class DynamicHtml(Observable):

    def __init__(self, directory, reactor=None, prefix = '', allowedModules=[], indexPage='', verbose=False):
        Observable.__init__(self)
        self._globals = None
        self._verbose = verbose
        self._directory = directory
        self._prefix = prefix
        self._indexPage = indexPage
        self._allowedModules = allowedModules
        self._modules = {}
        self._loadModuleFromPaths()
        self._initMonitoringForFileChanges(reactor)

    def _loadModuleFromPaths(self):
        for path in glob(self._directory + '/*.sf'):
            self.loadModuleFromPath(path)

    def _initMonitoringForFileChanges(self, reactor):
        directoryWatcher = DirectoryWatcher(
            self._directory,
            EventsCodes.IN_CREATE | EventsCodes.IN_MODIFY | EventsCodes.IN_MOVED_TO,
            self._notifyHandler)
        reactor.addReader(directoryWatcher, directoryWatcher)

    def _notifyHandler(self, event):
        self.loadModuleFromPath(join(self._directory, event.name))

    def loadModuleFromPath(self, path):
        moduleName = basename(path)[:-len('.sf')]
        basket = {}
        try:
            execfile(path, self.getGlobals(), basket)
        except Exception, e:
            s = escapeHtml(format_exc())
            basket['main'] = lambda *args, **kwargs: (x for x in ['<pre>', s, '</pre>'])
        self._modules[moduleName] = basket
        self._addModuleGlobalsToMain(basket)
        newModule = EmptyModule()
        newModule.__dict__ = self._modules[moduleName]
        self._replaceModuleReferencesInOtherModules(moduleName, newModule)

    def _addModuleGlobalsToMain(self, globals):
        main = globals['main']
        for globalName, globalValue in globals.items():
            if globalName not in main.func_globals:
                main.func_globals[globalName] = globalValue

    def _replaceModuleReferencesInOtherModules(self, symbolName, newModule):
        for module in self._modules.values():
            if 'main' in module:
                moduleMain = module['main']
                if symbolName in moduleMain.func_globals:
                    moduleMain.func_globals[symbolName] = newModule

    def __import__(self, moduleName, globals=None, locals=None, fromlist=None):
        if moduleName in self._allowedModules:
             moduleObject = __import__(moduleName)
        else:
            if not moduleName in self._modules:
                filename = moduleName.replace('.', '/') + '.sf'
                self.loadModuleFromPath(join(self._directory, filename))
            moduleObject = EmptyModule()
            moduleObject.__dict__ = self._modules[moduleName]

        globals[moduleName] = moduleObject

    def _createMainGenerator(self, path, headers, arguments):
        i = path.find('/')
        if i < 1:
            name = path
            nextGenerator =  (i for i in [])
        else:
            name = path[:i]
            nextGenerator = self._createMainGenerator(path[i+1:], headers, arguments)
        if not name in self._modules:
            raise DynamicHtmlException('File %s does not exist.' % path)
        module = self._modules[name]
        myLocals = {'headers': headers, 'arguments': arguments, 'pipe': nextGenerator}
        myGlobals = {'main': module['main']}
        exec 'generator = main(headers=headers, arguments=arguments, pipe=pipe)' in myGlobals, myLocals
        return myLocals['generator']

    def handleRequest(self, RequestURI=None, *args, **kwargs):
        scheme, netloc, path, query, fragments = urlsplit(RequestURI)
        arguments = parse_qs(query)
        headers = kwargs.get('Headers', {})

        return self.handleHttpRequest(scheme, netloc, path, query, fragments, arguments, headers=headers)

    def handleHttpRequest(self, scheme, netloc, path, query='', fragments='', arguments={}, headers={}):
        path = path[len(self._prefix):]
        if path == '/' and self._indexPage:
            path = self._indexPage
        try:
            generators = self._createMainGenerator(path[1:], headers, arguments)
            contentType = 'text/html'
            if path.endswith('.xml'):
                contentType = 'text/xml'

            yield 'HTTP/1.0 200 Ok\r\nContent-Type: %s; charset=utf-8\r\n\r\n' % contentType

            for line in compose(generators):
                yield line
        except DynamicHtmlException, e:
            yield 'HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\n' + str(e)
        except Exception:
            s = format_exc() #cannot be inlined
            yield "<pre>"
            yield escapeHtml(s)
            yield "</pre>"

    def getGlobals(self):
        if not self._globals:
            self._globals = {
                '__builtins__': {
                    '__import__': self.__import__,
                    # standard Python stuff
                    'str': str,
                    'int': int,
                    'float': float,
                    'len': len,
                    'False': False,
                    'True': True,
                    'min': min,
                    'max': max,
                    'ceil': ceil,
                    'unicode': unicode,
                    'range': range,
                    'enumerate': enumerate,
                    'map': map,
                    'sorted': sorted,
                    'cmp': cmp,

                    # observable stuff
                    'any': self.any,
                    'all': self.all,
                    'do': self.do,

                    # commonly used/needed methods
                    'escapeHtml': escapeHtml,
                    'escapeXml': escapeXml,
                    'bind_stream': lambda x:wrapp(bind_stream(x)),
                    'time': time,
                    'urlencode': lambda x: urlencode(x, doseq=True),
                    'decorate': decorate,
                    'dirwalk': dirwalk,
                    'dirname': dirname,
                    'basename': basename

                }
            }
        return self._globals