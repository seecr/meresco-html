## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017-2018, 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2017-2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
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

from seecr.test import SeecrTestCase
from meresco.html import Html, HtmlTable, Column, HtmlForm

class HtmlTest(SeecrTestCase):

    def testHtml(self):
        h = Html()
        self.assertEqualsWS('<html></html>', h.render())

    def testColumnBasics(self):
        self.maxDiff = None
        st = HtmlTable()
        st.addColumn(Column(label='Label'))
        st.addColumn(Column(label='<label>'))
        html = st.render(items=(1,2,3))
        self.assertEqualsWS(
            '<table>'
            '<thead>'
            '<tr><th>Label</th><th>&lt;label&gt;</th></tr>'
            '</thead>'
            '<tfoot></tfoot>'
            '<tbody>'
            '<tr><td>1</td><td>1</td></tr>'
            '<tr><td>2</td><td>2</td></tr>'
            '<tr><td>3</td><td>3</td></tr>'
            '</tbody>'
            '</table>', html)

    def testIndividualColumnRender(self):
        class MyColumn(Column):
            def cell_tag(self, **_):
                return self.tag('dif')
            def cell_content(self, **_):
                return str(_)
        c1 = MyColumn(label='na')
        self.assertEqual("<dif>{'item': 'ape'}</dif>", c1.render(item='ape'))

    def testMyOwnClassesEverywhere(self):
        class MyTable(HtmlTable):
            # kies maar, het kan op allerlei manieren. Ik denk: append, replace, delete, etc
            def table_tag(self, **kwargs):
                return HtmlTable.table_tag(self, **kwargs).append('class', 'my-table')
            def head_tag(self, **kwargs):
                return HtmlTable.head_tag(self, **kwargs).set('class', ['my-head'])
            def head_row_tag(self, **kwargs):
                return HtmlTable.head_row_tag(self, **kwargs).append('class', 'my-head-row')
            def row_tag(self, **kwargs):
                return HtmlTable.row_tag(self, **kwargs).append('class', 'my-row')
            def foot_tag(self, **kwargs):
                return HtmlTable.foot_tag(self, **kwargs).delete('tag')
        class Column1(Column):
            def head_tag(self, **kwargs):
                return Column.head_tag(self, **kwargs).append('class', 'my-head-cell')
            def cell_tag(self, **kwargs):
                return Column.cell_tag(self, **kwargs).append('class', 'my-cell').set('name', 'anchorname')
        t = MyTable()
        t.addColumn(Column1('c1'))
        html = t.render(items=('<a', [], {1:2}))
        self.assertEqualsWS(
                '<table class="my-table">'
                '<thead class="my-head"><tr class="my-head-row"><th class="my-head-cell">c1</th></tr></thead>'
                '<tbody>'
                    '<tr class="my-row"><td class="my-cell" name="anchorname">&lt;a</td></tr>'
                    '<tr class="my-row"><td class="my-cell" name="anchorname">[]</td></tr>'
                    '<tr class="my-row"><td class="my-cell" name="anchorname">{1: 2}</td></tr>'
                '</tbody></table>', html)

    def testMyOwnRendering(self):
        class CustomColumn(Column):
           def cell_content(self, item, parent, **kwargs):
               yield str(item).swapcase() + parent
        t = HtmlTable()
        t.addColumn(CustomColumn(label='c1'))
        html = t.render(items=['aa<p'], parent='fiets')
        self.assertEqualsWS(
                '<table>'
                '<thead><tr><th>c1</th></tr></thead>'
                '<tfoot></tfoot>'
                '<tbody>'
                    '<tr><td>AA&lt;Pfiets</td></tr>'
                '</tbody></table>', html)

    def testReuse(self):
        t = HtmlTable()
        t.addColumn(Column(label="c1"))
        html = t.render((1, 2))
        self.assertEqualsWS("<table><thead><tr><th>c1</th></tr></thead><tfoot></tfoot><tbody><tr><td>1</td></tr><tr><td>2</td></tr></tbody></table>", html)
        html = t.render((3, 4))
        self.assertEqualsWS("<table><thead><tr><th>c1</th></tr></thead><tfoot></tfoot><tbody><tr><td>3</td></tr><tr><td>4</td></tr></tbody></table>", html)

    def testColumnWithColspan(self):
        class OneHeadTwoCells(Column):
            def head_tag(self, **kwargs):
                return Column.head_tag(self).set('colspan', '2')
            def colspan(self):
                return 2
            def cell_tag(self, **kwargs):
                return self.tag(None)
            def cell_content(self, item, **kwargs):
                with self.tag('td'):
                    yield '1-{}'.format(item)
                with self.tag('td'):
                    yield '2-{}'.format(item)
        t = HtmlTable()
        t.addColumn(OneHeadTwoCells(label="label"))
        html = t.render(("a", "b"))
        self.assertEqualsWS('<table>'
            '<thead><tr><th colspan="2">label</th></tr></thead>'
            '<tfoot></tfoot>'
            '<tbody>'
            '<tr><td>1-a</td><td>2-a</td></tr>'
            '<tr><td>1-b</td><td>2-b</td></tr>'
            '</tbody>'
            '</table>', html)

    def testForm(self):
        form = HtmlForm('/action/some.thing')
        html = ''.join(form.render())
        self.assertEqual('<form action="/action/some.thing" method="POST" role="form"></form>', html)
        html = ''.join(form.render(hiddenData={"a":"b"}))
        self.assertEqual('<form action="/action/some.thing" method="POST" role="form"><input name="a" type="hidden" value="b"></form>', html)

    def testFromGroup(self):
        form = HtmlForm('/action/a.b')
        class FormGroup(object):
            def setForm(self, form):
                self.tag = form.tag
                return self
            def main(self, **kwargs):
                with self.tag('textarea', **{'name': 'input_name' }):
                    yield '<contents>'
        formGroup = FormGroup()
        form.addFormGroup(formGroup)
        group = ''.join(form.render(hiddenData={'identifier':'my_id'})) # rewrite formgroup
        self.assertEqual('<form action="/action/a.b" method="POST" role="form"><input name="identifier" type="hidden" value="my_id"><textarea name="input_name">&lt;contents&gt;</textarea></form>', group)

    def testSpecialTags(self):
        class Test(Html):
            def main(self, **kwargs):
                with self.tag('p'):
                    yield 'tekst'
                    with self.tag('br'):
                        yield ''
                    yield 'regel twee'
                with self.tag('hr'):
                    yield ''
                with self.tag('p'):
                    yield 'slot'
        self.assertEqual('<p>tekst<br/>regel twee</p><hr/><p>slot</p>', Test().render())

    def testClass_(self):
        class Test(Html):
            def main(self, **kwargs):
                with self.tag('p', class_=['a', 'b']):
                    yield 'text'
        self.assertEqual('<p class="a b">text</p>', Test().render())

    def testPrevCurNext(self):
        class PrevCurNextColumn(Column):
            def cell_content(self, item, prevItem, nextItem, **kwargs):
                yield '{} {} {}'.format(prevItem or '-', item, nextItem or '-')
        t = HtmlTable()
        t.addColumn(PrevCurNextColumn(label="label"))
        html = t.render([1,2,3])
        self.assertEqualsWS('<table>'
            '<thead><tr><th>label</th></tr></thead>'
            '<tfoot></tfoot>'
            '<tbody>'
            '<tr><td>- 1 2</td></tr>'
            '<tr><td>1 2 3</td></tr>'
            '<tr><td>2 3 -</td></tr>'
            '</tbody>'
            '</table>', html)

