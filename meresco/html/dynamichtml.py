# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2008-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2011-2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
#
# This file is part of "Meresco Html"
#
# "Meresco Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from glob import glob
from os.path import join, isfile, dirname, basename
from traceback import format_exc
from meresco.html.utils import parse_qs
from itertools import groupby, islice
from io import StringIO
from contextlib import contextmanager

from xml.sax.saxutils import escape as escapeXml, quoteattr
from lxml.etree import parse, tostring
from time import time
from urllib.parse import urlencode as _urlencode
from math import ceil
from functools import partial, reduce

from meresco.components.json import JsonList, JsonDict
from meresco.core import Observable, decorate

from weightless.core import compose, Yield, NoneOfTheObserversRespond

from meresco.components import DirectoryWatcher
import builtins as exceptions
from simplejson import dumps, loads
from urllib.parse import urlsplit, urlunsplit

from ._html import TagFactory, escapeHtml, tag_compose

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
        try:
            return self._globals[attr]
        except KeyError:
            raise AttributeError

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
    return HTTP_CODE + CRLF.join("{0}: {1}".format(*i) for i in headers.items()) + CRLF + CRLF

class Http(object):
    def redirect(self, location, additionalHeaders=None, permanent=False):
        return redirectTo(location, additionalHeaders=additionalHeaders, permanent=permanent)

def urlencode(query, doseq=True):
    return _urlencode(query, doseq)

class ObservableProxy(object):

    def __init__(self, observable):
        self.any = observable.any
        self.all = observable.all
        self.call = observable.call
        self.do = observable.do
        self.once = observable.once


class DynamicHtml(Observable):
    def __init__(self, directories, reactor=None, prefix='', allowedModules=None, indexPage='', verbose=False, additionalGlobals=None, notFoundPage=None, watch=True, errorHandlingHook=None):
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
        self._errorHandlingHook = errorHandlingHook
        self._initialize(reactor, watch=watch)

    def _loadAllTemplates(self):
        self._templates.clear()
        for directory in self._directories:
            for path in glob(directory + '/*.sf'):
                templateName = basename(path)[:-len('.sf')]
                self.loadTemplateModule(templateName)

    def _initialize(self, reactor, watch):
        self._loadAllTemplates()
        if reactor is not None and watch:
            for directory in self._directories:
                directoryWatcher = DirectoryWatcher(
                    directory,
                    self._notifyHandler,
                    CreateFile=True, ModifyFile=True, MoveInFile=True)
                reactor.addReader(directoryWatcher, directoryWatcher)

    def _notifyHandler(self, event):
        if not event.name.endswith('.sf'):
            return
        self._loadAllTemplates()

    def _pathForTemplateName(self, name):
        for directory in self._directories:
            path = join(directory, '%s.sf' % name)
            if isfile(path):
                return path

    def loadTemplateModule(self, templateName):
        if templateName in self._templates:
            return

        def load():
            moduleGlobals = self.createGlobals()
            createdLocals = {}
            try:
                path = self._pathForTemplateName(templateName)
                with open(path, "rb") as f:
                    exec(compile(f.read(), path, 'exec'), moduleGlobals, createdLocals)
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
            def _():
                yield self._createMainGenerator(nextHead, nextTail, scheme=scheme, netloc=netloc, path=path, query=query, Headers=Headers, arguments=arguments, **kwargs)
            nextGenerator = _()

        if not head in self._templates or not hasattr(self._templates[head], 'main'):
            raise DynamicHtmlException.notFound(head)
        main = self._templates[head].main

        def _():
            yield main(scheme=scheme, netloc=netloc, path=path, query=query, Headers=Headers, arguments=arguments, pipe=nextGenerator, **kwargs)

        return _()

    def _splitPath(self, aPath):
        normalizedPath = '/'.join(p for p in aPath.split('/') if p)
        if '/' in normalizedPath:
            return normalizedPath[:normalizedPath.index('/')], normalizedPath[normalizedPath.index('/'):]
        return normalizedPath, None

    def _createGenerators(self, path, not_found_originalPath=None, scheme='', **kwargs):
        head, tail = self._splitPath(path)
        if not head in self._templates:
            raise DynamicHtmlException.notFound(head)
        return compose(self._createMainGenerator(
            head, tail,
            path=(not_found_originalPath if not_found_originalPath is not None else path),
            **kwargs))

    @compose
    def handleRequest(self, path='', **kwargs):
        path = path[len(self._prefix):]
        if path == '/' and self._indexPage:
            newLocation = self._indexPage
            arguments = kwargs.get('arguments', {})
            if arguments:
                newLocation = '%s?%s' % (newLocation, urlencode(arguments, doseq=True))
            yield redirectTo(newLocation)
            return

        tag = TagFactory()
        kwargs.update(tag=tag)

        try:
            generators = self._createGenerators(path, **kwargs)
        except DynamicHtmlException as e:
            if self._notFoundPage is None:
                yield e.httpHeader()
                yield str(e)
                return
            try:
                generators = self._createGenerators(self._notFoundPage, not_found_originalPath=path, **kwargs)
            except DynamicHtmlException as innerException:
                yield innerException.httpHeader()
                yield str(innerException)
                return
        except Exception as e:
            if self._errorHandlingHook:
                s = format_exc() #cannot be inlined
                response = self._errorHandlingHook(s, path, **kwargs)
                if not response is None:
                    yield response
                    return
            raise e

        while True:
            try:
                firstValue = next(generators)
                if firstValue is Yield or callable(firstValue):
                    yield firstValue
                    continue
                firstLine = str(firstValue)
                if not firstLine.startswith('HTTP/1.'):
                    contentType = 'text/html'
                    if path.endswith('.xml'):
                        contentType = 'text/xml'
                    yield 'HTTP/1.0 200 OK\r\nContent-Type: %s; charset=utf-8\r\n\r\n' % contentType
                yield tag.lines()
                yield tag.escape(firstLine)
                break
            except DynamicHtmlException as dhe:
                s = format_exc() #cannot be inlined
                yield dhe.httpHeader()
                yield str(s)
                return
            except Exception:
                s = format_exc() #cannot be inlined
                if self._errorHandlingHook:
                    response = self._errorHandlingHook(s, path, **kwargs)
                    if not response is None:
                        yield response
                        return
                yield 'HTTP/1.0 500 Internal Server Error\r\n\r\n'
                yield str(s)
                return

        try:
            for line in generators:
                yield tag.lines()
                yield line if line is Yield or callable(line) else tag.escape(line)
            yield tag.lines()
        except Exception:
            s = format_exc() #cannot be inlined
            if self._errorHandlingHook:
                response = self._errorHandlingHook(s, path, **kwargs)
                if not response is None:
                    yield response
                    return
            yield "<pre>"
            yield escapeHtml(s)
            yield "</pre>"

    def getModule(self, name):
        return self._templates.get(name)

    def createGlobals(self):
        result = self._additionalGlobals.copy()
        result.update({
            # Allow class creaton
            '__module__': '__dynamichtml__',
            '__name__': '__dynamichtml__',
        })
        result['__builtins__'] = {
            '__import__': self.__import__,
            'importTemplate': lambda templateName: self.__import__(templateName),

            # standard Python stuff
            'Ellipsis': Ellipsis,
            'Exception': Exception,
            'False': False,
            'None': None,
            'NotImplemented': NotImplemented,
            'True': True,
            'abs': abs,
            'all': all,
            'any': any,
            'basestring': str,
            'bin': bin,
            'bool': bool,
            'buffer': memoryview, # not sure if memoryview is 100% compatible with buffer
            'bytearray': bytearray,
            'callable': callable,
            'ceil': ceil,
            'chr': chr,
            'classmethod': classmethod,
            #'cmp': cmp, deprecated
            #'coerce': coerce,
            'complex': complex,
            'delattr': delattr,
            'dict': dict,
            'dir': dir,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'frozenset': frozenset,
            'getattr': getattr,
            'globals': globals,
            'groupby': groupby,
            'hasattr': hasattr,
            'hash': hash,
            'hex': hex,
            'id': id,
            'int': int,
            #'intern': intern,
            'isinstance': isinstance,
            'islice': islice,
            'issubclass': issubclass,
            '__build_class__': __build_class__,
            'iter': iter,
            'len': len,
            'list': list,
            'locals': locals,
            'long': int,
            'map': map,
            'max': max,
            'memoryview': memoryview, # duplicate, see buffer
            'min': min,
            'next': next,
            'object': object,
            'oct': oct,
            'ord': ord,
            'partial': partial,
            'pow': pow,
            'property': property,
            'range': range,
            'reduce': reduce,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'setattr': setattr,
            'slice': slice,
            'sorted': sorted,
            'staticmethod': staticmethod,
            'str': str,
            'sum': sum,
            'super': super,
            'tuple': tuple,
            'type': type,
            'unichr': chr,
            'unicode': str,
            'vars': vars,
            'xrange': range,
            'zip': zip,

            # weightless stuff
            'Yield': Yield,

            # observables proxy
            'observable': self._observableProxy,
            'NoneOfTheObserversRespond': NoneOfTheObserversRespond,

            'tag_compose': tag_compose,

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
            'JsonDict': JsonDict,
            'JsonList': JsonList,
            'urlsplit': urlsplit,
            'urlunsplit': urlunsplit,
            'DynamicHtmlException': DynamicHtmlException,
        }
        result['__builtins__'].update((excName, excType) for excName, excType in vars(exceptions).items() if not excName.startswith('_'))
        return result
