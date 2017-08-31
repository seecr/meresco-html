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

from seecr.test import SeecrTestCase, CallTrace
from meresco.html import Tag, DynamicHtml
from meresco.html._html._tag import _clearname as clear
from meresco.components.http.utils import parseResponse
from weightless.core import asString
from StringIO import StringIO

class TagTest(SeecrTestCase):
    def testAttrs(self):
        s = StringIO()
        with Tag(s, 'a', **{'key': 'value'}):
            s.write('data')
        self.assertEqual('<a key="value">data</a>', s.getvalue())

    def testClearName(self):
        self.assertEquals('class', clear('class'))
        self.assertEquals('class', clear('class_'))
        self.assertEquals('_class', clear('_class'))
        self.assertEquals('_class_', clear('_class_'))
        self.assertEquals('class__', clear('class__'))

    def testReservedWordAttrs(self):
        s = StringIO()
        with Tag(s, 'a', class_=['class'], if_='if'):
            s.write('data')
        self.assertEqual('<a class="class" if="if">data</a>', s.getvalue())

    def testTagInTemplate(self):
        self.assertEqual('voorwoord<p>paragraph</p>nawoord', self.processTemplate('''
                yield 'voorwoord'
                with tag('p'):
                    yield 'paragraph'
                yield 'nawoord'
            '''))
        self.assertEqual('voorwoord<p><i>italic</i></p>', self.processTemplate('''
                yield 'voorwoord'
                with tag('p'):
                    with tag('i'):
                        yield 'italic'
            '''))
        self.assertEqual('<p><i>italic</i></p>', self.processTemplate('''
                with tag('p'):
                    with tag('i'):
                        yield 'italic'
            '''))

    def testEscapeTextWithinTags(self):
        self.assertEqual('&', self.processTemplate('  yield "&"'))
        self.assertEqual('&<p>&amp;</p>', self.processTemplate('''
            yield "&"
            with tag('p'):
                yield "&"
        '''))
        self.assertEqual('&a<p>&amp;b &amp;c</p>&d', self.processTemplate('''
            yield "&a"
            with tag('p'):
                yield "&b"
                yield " &c"
            yield "&d"
        '''))
        self.assertEqual('<p>&amp;a &amp;b</p>', self.processTemplate('''
            with tag('p'):
                yield "&a"
                yield " &b"
        '''))
        self.assertEqual('<p>&amp;a<i>&amp;b</i>&amp;c</p>&d', self.processTemplate('''
            with tag('p'):
                yield "&a"
                with tag('i'):
                    yield "&b"
                yield "&c"
            yield "&d"
        '''))
        self.assertEqual('<p>&amp;a</p>&b<p>&amp;c</p>&d', self.processTemplate('''
            with tag('p'):
                yield "&a"
            yield "&b"
            with tag('p'):
                yield "&c"
            yield "&d"
        '''))

    def testEscapeOtherStuff(self):
        self.assertEqual("<p>['&amp;', 'noot']</p>", self.processTemplate('''
            with tag('p'):
                yield ['&', 'noot']
        '''))

    def testAsIs(self):
        self.assertEqual('<p><i>dit</i></p>', self.processTemplate('''
            with tag('p'):
                yield tag.as_is('<i>dit</i>')
        '''))

   # with escape firstline

    def processTemplate(self, template):
        open(self.tempdir+'/afile.sf', 'w').write('def main(tag, **kwargs):\n'+template)
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        header, body = parseResponse(asString(d.handleRequest(path='/afile')))
        self.assertEqual('200', header['StatusCode'])
        return body

