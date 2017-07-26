## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017 Seecr (Seek You Too B.V.) http://seecr.nl
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

from weightless.core import compose
from cStringIO import StringIO
from meresco.html.dynamichtml import escapeHtml
from xml.sax.saxutils import quoteattr

class Html(object):

    def write(self, data):
        self._buf.write(data)

    def render(self, *args, **kwargs):
        self._buf = StringIO()
        for line in compose(self.main(*args, **kwargs)):
            self.write(escapeHtml(line))
        return self._buf.getvalue()

    def main(self, *args, **kwargs):
        with self.tag('html'):
            yield ''

    def tag(self, tagname, **attrs):
        attrs.setdefault('class', [])
        return self.Tag(self._buf.write, tagname, attrs)

    class Tag(object):
        def __init__(self, write, tagname, attrs):
            self.attrs = attrs
            self.write = write
            self.attrs['tag'] = tagname

        def set(self, name, value):
            self.attrs[name] = value
            return self

        def append(self, name, value):
            self.attrs[name].append(value)
            return self

        def delete(self, key):
            self.attrs.pop(key, None)
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
            write('>')

        def __exit__(self, *a, **kw):
            if self.tag:
                write = self.write
                write('</')
                write(self.tag)
                write('>')

