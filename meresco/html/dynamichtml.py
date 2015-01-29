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

from glob import glob
from os.path import join, isfile, dirname, basename
from traceback import format_exc
from cgi import parse_qs
from itertools import groupby, islice

from functools import partial, reduce
from html import escape as _escapeHtml
from lxml.etree import parse, tostring
from math import ceil
from time import time
from urllib.parse import urlencode as _urlencode
from xml.sax.saxutils import escape as escapeXml, quoteattr

from meresco.core import Observable, decorate

from weightless.core import compose, Yield

from meresco.components import DirectoryWatcher
from simplejson import dumps, loads
from urllib.parse import urlsplit, urlunsplit
import collections

CRLF = '\r\n'

class TemplateModule(object):
    def __init__(self, load):
        self._loadGlobals = load
        self._globals = None

    def _mustReload(self):
        self._globals = None

    def __getattr__(self, attr):
        if self._globals is None:
            self._globals = self._loadGlobals()
        return self._globals[attr]

    def __setattr__(self, name, value):
        if name in ['_loadGlobals', '_globals']:
            return object.__setattr__(self, name, value)
        raise AttributeError("Set of an attribute is not allowed on a TemplateModule")

class DynamicHtmlException(Exception):
    httpCodes = {
        500: 'Internal Server Error',
        404: 'Not Found',
    }
    def __init__(self, message, httpCode=500):
        super(DynamicHtmlException, self).__init__(message)
        self._httpCode = httpCode if httpCode in self.httpCodes else 500

    @classmethod
    def notFound(cls, filename):
        return cls('File "%s" does not exist.' % filename, httpCode=404)

    def httpHeader(self):
        yield 'HTTP/1.0 {code} {httpCodeText}\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'.format(
                code=self._httpCode,
                httpCodeText=self.httpCodes[self._httpCode]
            )

def redirectTo(location, additionalHeaders=None, permanent=False):
    HTTP_CODE = "HTTP/1.0 302 Found\r\n"
    if permanent:
        HTTP_CODE = "HTTP/1.0 301 Moved Permanently\r\n"
    headers = {'Location': location}
    if not additionalHeaders is None:
        headers.update(additionalHeaders)
    return HTTP_CODE + CRLF.join("{0}: {1}".format(*i) for i in list(headers.items())) + CRLF + CRLF

class Http(object):
    def redirect(self, location, additionalHeaders=None, permanent=False):
        return redirectTo(location, additionalHeaders=additionalHeaders, permanent=permanent)

def escapeHtml(aString):
    return _escapeHtml(aString).replace('"','&quot;')

def _stringify(values):
    if isinstance(values, str):
        return str(values)
    try:
        return [str(value) for value in values]
    except TypeError: # not iterable
        return str(values)

def urlencode(query, doseq=True):
    if not doseq:
        return _urlencode(query, doseq)
    if hasattr(query, 'items'):
        query = list(query.items())
    return _urlencode([(k,_stringify(v)) for k,v in query], doseq)

class ObservableProxy(object):

    def __init__(self, observable):
        self.any = observable.any
        self.all = observable.all
        self.call = observable.call
        self.do = observable.do
        self.once = observable.once


class DynamicHtml(Observable):
    def __init__(self, directories, reactor=None, prefix='', allowedModules=None, indexPage='', verbose=False, additionalGlobals=None, notFoundPage=None):
        Observable.__init__(self)
        self._verbose = verbose
        if type(directories) != list:
            raise TypeError("Usage: DynamicHtml([aDirectory, ...], ....)")
        self._directories = directories
        self._prefix = prefix
        self._indexPage = indexPage
        self._notFoundPage = notFoundPage
        self._allowedModules = allowedModules or []
        self._templates = {}
        self._additionalGlobals = additionalGlobals or {}
        self._observableProxy = ObservableProxy(self)
        self._initialize(reactor)

    def _initialize(self, reactor):
        for directory in self._directories:
            for path in glob(directory + '/*.sf'):
                templateName = basename(path)[:-len('.sf')]
                self.loadTemplateModule(templateName)
            directoryWatcher = DirectoryWatcher(
                directory,
                self._notifyHandler,
                CreateFile=True, ModifyFile=True, MoveInFile=True)
            reactor.addReader(directoryWatcher, directoryWatcher)

    def _notifyHandler(self, event):
        if not event.name.endswith('.sf'):
            return
        templateName = basename(event.name)[:-len('.sf')]
        self.loadTemplateModule(templateName)

    def _pathForTemplateName(self, name):
        for directory in self._directories:
            path = join(directory, '%s.sf' % name)
            if isfile(path):
                return path

    def loadTemplateModule(self, templateName):
        if templateName in self._templates:
            self._templates[templateName]._mustReload()
        else:
            def load():
                moduleGlobals = self.createGlobals()
                createdLocals = {}
                try:
                    path = self._pathForTemplateName(templateName)
                    with open(path) as fp:
                        exec(compile(fp.read(), path, 'exec'), moduleGlobals, createdLocals)
                except Exception:
                    s = escapeHtml(format_exc())
                    createdLocals['main'] = lambda *args, **kwargs: (x for x in ['<pre>', s, '</pre>'])
                moduleGlobals.update(createdLocals)
                return moduleGlobals
            self._templates[templateName] = TemplateModule(load)

    def __import__(self, moduleName, globals=None, locals=None, fromlist=None, level=None):
        if moduleName in self._allowedModules:
            return __import__(moduleName)
        if not moduleName in self._templates:
            # TS: Required for out-of-initial-loading-order importing of
            #     another template (at initialize()-time).
            self.loadTemplateModule(moduleName)
        return self._templates[moduleName]

    def _createMainGenerator(self, head, tail, scheme='', netloc='', path='', query='', Headers=None, arguments=None, **kwargs):
        Headers = Headers or {}
        arguments = arguments or {}
        if tail == None:
            nextGenerator =  (i for i in [])
        else:
            nextHead, nextTail = self._splitPath(tail)
            nextGenerator = self._createMainGenerator(nextHead, nextTail, scheme=scheme, netloc=netloc, path=path, query=query, Headers=Headers, arguments=arguments, **kwargs)
        try:
            main = self._templates[head].main
        except:
            raise DynamicHtmlException.notFound(head)
        yield main(scheme=scheme, netloc=netloc, path=path, query=query, Headers=Headers, arguments=arguments, pipe=nextGenerator, **kwargs)

    def _splitPath(self, aPath):
        normalizedPath = '/'.join(p for p in aPath.split('/') if p)
        if '/' in normalizedPath:
            return normalizedPath[:normalizedPath.index('/')], normalizedPath[normalizedPath.index('/'):]
        return normalizedPath, None

    def _createGenerators(self, path, scheme='', **kwargs):
        head, tail = self._splitPath(path)
        if not head in self._templates:
            raise DynamicHtmlException.notFound(head)
        return compose(self._createMainGenerator(head, tail, path=path, **kwargs))

    def handleRequest(self, path='', **kwargs):
        path = path[len(self._prefix):]
        if path == '/' and self._indexPage:
            newLocation = self._indexPage
            arguments = kwargs.get('arguments', {})
            if arguments:
                newLocation = '%s?%s' % (newLocation, urlencode(arguments, doseq=True))
            yield redirectTo(newLocation)
            return

        try:
            generators = self._createGenerators(path, **kwargs)
        except DynamicHtmlException as e:
            if self._notFoundPage is None:
                yield e.httpHeader()
                yield str(e)
                return
            try:
                generators = self._createGenerators(self._notFoundPage, **kwargs)
            except DynamicHtmlException as innerException:
                yield innerException.httpHeader()
                yield str(innerException)
                return

        while True:
            try:
                firstValue = next(generators)
                if firstValue is Yield or isinstance(firstValue, collections.Callable):
                    yield firstValue
                    continue
                firstLine = str(firstValue)
                if not firstLine.startswith('HTTP/1.'):
                    contentType = 'text/html'
                    if path.endswith('.xml'):
                        contentType = 'text/xml'
                    yield 'HTTP/1.0 200 OK\r\nContent-Type: %s; charset=utf-8\r\n\r\n' % contentType
                yield firstLine
                break
            except DynamicHtmlException as dhe:
                s = format_exc() #cannot be inlined
                yield dhe.httpHeader()
                yield str(s)
                return
            except Exception:
                s = format_exc() #cannot be inlined
                yield 'HTTP/1.0 500 Internal Server Error\r\n\r\n'
                yield str(s)
                return

        try:
            for line in generators:
                yield line if line is Yield or isinstance(line, collections.Callable) else str(line)
        except Exception:
            s = format_exc() #cannot be inlined
            yield "<pre>"
            yield escapeHtml(s)
            yield "</pre>"

    def getModule(self, name):
        return self._templates.get(name)

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
            'unicode': str,
            'range': range,
            'xrange': lambda *args, **kwargs: NoLongerSupported("xrange"),
            'reduce': reduce,
            'reversed': reversed,
            'zip': zip,
            'enumerate': enumerate,
            'map': map,
            'sorted': sorted,
            'cmp': lambda *args, **kwargs: NoLongerSupported("cmp"),
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

            # weightless stuff
            'Yield': Yield,

            # observables proxy
            'observable': self._observableProxy,

            # commonly used/needed methods
            'escapeHtml': escapeHtml,
            'quoteattr': quoteattr,
            'escapeXml': escapeXml,
            'time': time,
            'urlencode': urlencode,
            'decorate': decorate,
            'dirname': dirname,
            'basename': basename, 
            'parse_qs': parse_qs, 
            'parse': parse, 
            'tostring': tostring, 
            'http': Http(), 
            'dumps': dumps, 
            'loads': loads, 
            'urlsplit': urlsplit, 
            'urlunsplit': urlunsplit, 
            'DynamicHtmlException': DynamicHtmlException, 
        } 
        result['__builtins__'].update((e.__name__, e) for e in Exception.__subclasses__())

        return result

def NoLongerSupported(msg):
    raise NotImplementedError("{0} is not supported in python3".format(msg))