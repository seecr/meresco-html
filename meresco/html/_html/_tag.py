## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017-2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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

from io import StringIO
from functools import partial
from xml.sax.saxutils import quoteattr
import re
from contextlib import contextmanager
from ._utils import escapeHtml
from weightless.core import compose
from warnings import warn

def isiter(a):
    try:
        iter(a)
    except TypeError:
        return False
    return True

class Tag(object):
    def __init__(self, html, tagname, _enter_callback=lambda: None, _exit_callback=lambda: None, **attrs):
        self.attrs = {_clearname(k):v for k,v in list(attrs.items())}
        self.html = html
        self._enter_callback = _enter_callback
        self._exit_callback = _exit_callback
        self.attrs['tag'], id_, classes = _splittag(tagname)
        if id_:
            self.set('id', id_)
        for c in classes:
            self.append('class', c)
        self.as_is = AsIs

    def set(self, name, value):
        self.attrs[_clearname(name)] = value
        return self

    def append(self, name, value):
        k = _clearname(name)
        v = self.attrs.get(k)
        if v is None:
            self.attrs[k] = v = []
        v.append(value)
        return self

    def remove(self, name, value):
        self.attrs[_clearname(name)].remove(value)
        return self

    def delete(self, key):
        self.attrs.pop(_clearname(key), None)
        return self

    def __enter__(self):
        self._enter_callback()
        self.tag = self.attrs.pop('tag', None)
        if not self.tag:
            return
        write = self.html.write
        write('<')
        write(self.tag)
        for k, v in sorted((k,v) for k,v in self.attrs.items() if v):
            write(' ')
            write(k)
            write('=')
            if isiter(v) and not isinstance(v, str):
                write(quoteattr(' '.join(str(i) for i in v)))
            else:
                write(quoteattr(str(v)))
        if self.tag in ['br', 'hr']:
            write('/')
            self.tag = None
        if self.tag in ['input']:
            self.tag = None
        write('>')

    def __exit__(self, *a, **kw):
        self._exit_callback()
        if self.tag:
            write = self.html.write
            write('</')
            write(self.tag)
            write('>')

class TagFactory(object):
    def __init__(self):
        self.stream = StringIO()
        self._count = 0

    def write(self, d):
        return self.stream.write(d)

    def _enter_callback(self):
        self._count += 1

    def _exit_callback(self):
        self._count -= 1

    def __call__(self, *args, **kwargs):
        return Tag(self, _enter_callback=self._enter_callback, _exit_callback=self._exit_callback, *args, **kwargs)

    def lines(self):
        if self.stream.tell():
            yield self.stream.getvalue()
            self.stream.truncate(0)
            self.stream.seek(0)

    def escape(self, obj):
        if self._count:
            return escapeHtml(str(obj))
        return str(obj)

    def as_is(self, obj):
        return AsIs(obj)

    def compose(self, f):
        return partial(tag_compose(f, __bw_compat__=True), self)

def tag_compose(f, __bw_compat__=False):
    @contextmanager
    @compose
    def ctx_man(tag, *args, **kwargs):
        tag._enter_callback()
        try:
            g = compose(f(*args, **kwargs) if __bw_compat__ else f(tag, *args, **kwargs))
            for line in g:
                if line == None:
                    break
                tag.stream.write(escapeHtml(str(line)))
            yield
            for line in g:
                tag.stream.write(escapeHtml(str(line)))
        finally:
            tag._exit_callback()
    return ctx_man

class AsIs(str):
    def replace(self, *args):
        return self
    def __str__(self):
        return self

_CLEAR_RE = re.compile(r'^([^_].*[^_])_$')
def _clearname(name):
    m = _CLEAR_RE.match(name)
    if m:
        return m.group(1)
    return name

def _splittag(tagname):
    if not tagname:
        return tagname, None, []
    tagname, _, classstring = tagname.partition('.')
    tagname, _, identifier = tagname.partition('#')
    return tagname, identifier, [c for c in classstring.split('.') if c]
