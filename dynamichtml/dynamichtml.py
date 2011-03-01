# -*- coding: utf-8 -*-
## begin license ##
#
#    DynamicHtml is a template engine based on generators, and a sequel to Slowfoot.
#    Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of DynamicHtml.
#
#    DynamicHtml is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    DynamicHtml is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with DynamicHtml; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from glob import glob
from os.path import join, isfile, dirname, basename
from traceback import format_exc
from cgi import parse_qs
from itertools import groupby, islice

from cgi import escape as _escapeHtml
from xml.sax.saxutils import escape as escapeXml
from amara.binderytools import bind_stream
from lxml.etree import parse, tostring
from time import time
from urllib import urlencode
from math import ceil
from functools import partial

from meresco.core import Observable, decorate

from weightless.core import compose

from cq2utils.wrappers import wrapp
from cq2utils import DirectoryWatcher

class Module:
    def __init__(self, moduleGlobals):
        self.__dict__ = moduleGlobals

class DynamicHtmlException(Exception):
    pass

class Http(object):
    def redirect(self, location):
        return "HTTP/1.0 302 Found\r\nLocation: %(location)s\r\n\r\n" % locals()

def escapeHtml(aString):
    return _escapeHtml(aString).replace('"','&quot;')

class DynamicHtml(Observable):

    def __init__(self, directories, reactor=None, prefix = '', allowedModules=None, indexPage='', verbose=False, additionalGlobals=None):
        Observable.__init__(self)
        self._verbose = verbose
        if type(directories) != list:
            raise TypeError("Usage: DynamicHtml([aDirectory, ...], ....)")
        self._directories = directories
        self._prefix = prefix
        self._indexPage = indexPage
        self._allowedModules = allowedModules or []
        self._modules = {}
        self._initMonitoringForFileChanges(reactor)
        self._additionalGlobals = additionalGlobals or {}

    def _loadModuleFromPaths(self):
        for directory in reversed(self._directories):
            for path in glob(directory + '/*.sf'):
                self.loadModuleFromPath(path)

    def _initMonitoringForFileChanges(self, reactor):
        for directory in self._directories:
            directoryWatcher = DirectoryWatcher(
                directory,
                self._notifyHandler,
                CreateFile=True, ModifyFile=True, MoveInFile=True)
            reactor.addReader(directoryWatcher, directoryWatcher)

    def _notifyHandler(self, event):
        if not self._modules:
            self._loadModuleFromPaths()
        for directory in reversed(self._directories):
            templateFile = join(directory, event.name)
            if isfile(templateFile):
                self.loadModuleFromPath(templateFile)

    def loadModuleFromPath(self, path):
        moduleName = basename(path)[:-len('.sf')]
        moduleGlobals = self.createGlobals()
        createdLocals = {}
        success = False
        try:
            execfile(path, moduleGlobals, createdLocals)
            success = True
        except Exception, e:
            s = escapeHtml(format_exc())
            createdLocals['main'] = lambda *args, **kwargs: (x for x in ['<pre>', s, '</pre>'])
        moduleGlobals.update(createdLocals)
        newModule = Module(moduleGlobals)
        self._replaceModuleReferencesInOtherModules(moduleName, newModule)
        self._modules[moduleName] = newModule
        return success

    def _replaceModuleReferencesInOtherModules(self, moduleName, newModule):
        for module in self._modules.values():
            if moduleName in module.__dict__:
                module.__dict__[moduleName] = newModule

    def __import__(self, moduleName, globals=None, locals=None, fromlist=None):
        if moduleName in self._allowedModules:
            moduleObject = __import__(moduleName)
        else:
            if not moduleName in self._modules:
                filename = moduleName.replace('.', '/') + '.sf'
                for directory in self._directories:
                    if self.loadModuleFromPath(join(directory, filename)):
                        break
            moduleObject = self._modules[moduleName]
        return moduleObject

    def _getModules(self):
        if not self._modules:
            self._loadModuleFromPaths()
        return self._modules

    def _createMainGenerator(self, head, tail, Headers, arguments, **kwargs):
        if tail == None:
            nextGenerator =  (i for i in [])
        else:
            nextHead, nextTail = self._splitPath(tail)
            nextGenerator = self._createMainGenerator(nextHead, nextTail, Headers=Headers, arguments=arguments, **kwargs)
        modules = self._getModules()
        main = modules[head].main
        yield main(Headers=Headers, arguments=arguments, pipe=nextGenerator, **kwargs)

    def _splitPath(self, aPath):
        normalizedPath = '/'.join(p for p in aPath.split('/') if p)
        if '/' in normalizedPath:
            return normalizedPath[:normalizedPath.index('/')], normalizedPath[normalizedPath.index('/'):]
        return normalizedPath, None

    def handleRequest(self, scheme='', netloc='', path='', query='', fragments='', arguments={}, Headers={}, **kwargs):

        path = path[len(self._prefix):]
        if path == '/' and self._indexPage:
            newLocation = self._indexPage
            if arguments:
                newLocation = '%s?%s' % (newLocation, urlencode(arguments, doseq=True))
            yield "HTTP/1.0 302 Found\r\nLocation: %s\r\n\r\n" % newLocation
            return

        try:
            head, tail = self._splitPath(path)
            if not head in self._getModules():
                raise DynamicHtmlException('File "%s" does not exist.' % head)
            generators = compose(self._createMainGenerator(head, tail, Headers=Headers, arguments=arguments, path=path, scheme=scheme, netloc=netloc, query=query, **kwargs))
        except DynamicHtmlException, e:
            yield 'HTTP/1.0 404 File not found\r\nContent-Type: text/html; charset=utf-8\r\n\r\n' + str(e)
            return

        while True:
            try:
                firstValue = generators.next()
                if callable(firstValue):
                    yield firstValue
                    continue
                firstLine = str(firstValue)
                if not firstLine.startswith('HTTP/1.'):
                    contentType = 'text/html'
                    if path.endswith('.xml'):
                        contentType = 'text/xml'
                    yield 'HTTP/1.0 200 Ok\r\nContent-Type: %s; charset=utf-8\r\n\r\n' % contentType
                yield firstLine
                break
            except Exception:
                s = format_exc() #cannot be inlined
                yield 'HTTP/1.0 500 Internal Server Error\r\n\r\n'
                yield str(s)
                return

        try:
            for line in generators:
                yield line if callable(line) else str(line)
        except Exception:
            s = format_exc() #cannot be inlined
            yield "<pre>"
            yield escapeHtml(s)
            yield "</pre>"

    def createGlobals(self):
        result = self._additionalGlobals.copy()
        result['__builtins__'] = {
            '__import__': self.__import__,
            'importTemplate': lambda templateName: self.__import__(templateName),
            # standard Python stuff
            'str': str,
            'repr': repr,
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
            'reduce': reduce,
            'reversed': reversed,
            'zip': zip,
            'enumerate': enumerate,
            'map': map,
            'sorted': sorted,
            'cmp': cmp,
            'dict': dict,
            'set': set,
            'list': list,
            'id': id,
            'partial': partial,
            'groupby': groupby,
            'islice': islice,
            'Exception': Exception,
            'locals': locals,
            'type': type,

            # observable stuff
            'any': self.any,
            'all': self.all,
            'do': self.do,
            'asyncdo': self.asyncdo,
            'asyncany': self.asyncany,

            # commonly used/needed methods
            'escapeHtml': escapeHtml,
            'escapeXml': escapeXml,
            'bind_stream': lambda x:wrapp(bind_stream(x)),
            'compose': compose,
            'time': time,
            'urlencode': lambda x: urlencode(x, doseq=True),
            'decorate': decorate,
            'dirname': dirname,
            'basename': basename,
            'parse_qs': parse_qs,
            'parse': parse,
            'tostring': tostring,
            'http': Http()
        }
        return result
