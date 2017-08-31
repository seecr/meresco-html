## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
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

from xml.sax.saxutils import quoteattr
import re

class Tag(object):
    def __init__(self, write, tagname, **attrs):
        self.attrs = {_clearname(k):v for k,v in attrs.items()}
        self.write = write
        self.attrs['tag'] = tagname

    def set(self, name, value):
        self.attrs[_clearname(name)] = value
        return self

    def append(self, name, value):
        self.attrs[_clearname(name)].append(value)
        return self

    def delete(self, key):
        self.attrs.pop(_clearname(key), None)
        return self

    def __enter__(self):
        self.tag = self.attrs.pop('tag', None)
        if not self.tag:
            return
        write = self.write
        write('<')
        write(self.tag)
        for k, v in sorted((k,v) for k,v in self.attrs.iteritems() if v):
            write(' ')
            write(k)
            write('=')
            write(quoteattr(' '.join(v) if hasattr(v, '__iter__') else v))
        if self.tag in ['br', 'hr']:
            write('/')
            self.tag = None
        if self.tag in ['input']:
            self.tag = None
        write('>')

    def __exit__(self, *a, **kw):
        if self.tag:
            write = self.write
            write('</')
            write(self.tag)
            write('>')

class TagFactory(object):
    def __init__(self, stream):
        self.stream = stream
    def __call__(self, *args, **kwargs):
        return Tag(self.stream.write, *args, **kwargs)

_CLEAR_RE = re.compile(r'^([^_].*[^_])_$')
def _clearname(name):
    m = _CLEAR_RE.match(name)
    if m:
        return m.group(1)
    return name
