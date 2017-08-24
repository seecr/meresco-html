## begin license ##
#
# "Sharekit" is a repository service for higher education in The Netherlands.
# The service is developed by Seecr for SURFmarket.
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Sharekit"
#
# "Sharekit" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Sharekit" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Sharekit"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from weightless.core import compose
from cStringIO import StringIO
from meresco.html.dynamichtml import escapeHtml
from meresco.html.tag import Tag

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
        return Tag(self._buf.write, tagname, attrs)

class HtmlTable(Html):

    def __init__(self):
        self.columns = []

    def addColumn(self, column):
        self.columns.append(column.setTable(self))

    def main(self, items, **kwargs):
        with self.table_tag(items=items, **kwargs):
            yield self.table_content(items=items, **kwargs)

    def table_tag(self, **kwargs):
        return self.tag('table')

    def table_content(self, **kwargs):
        with self.head_tag(**kwargs):
            yield self.head_content(**kwargs)
        with self.foot_tag(**kwargs):
            yield self.foot_content(**kwargs)
        with self.body_tag(**kwargs):
            yield self.body_content(**kwargs)

    def head_tag(self, **kwargs):
        return self.tag('thead')

    def head_content(self, **kwargs):
        with self.head_row_tag(**kwargs):
            yield self.head_row_content(**kwargs)

    def head_row_tag(self, **kwargs):
        return self.tag('tr')

    def head_row_content(self, **kwargs):
        for column in self.columns:
            with column.head_tag(**kwargs):
                yield column.head_content(**kwargs)

    def body_tag(self, **kwargs):
        return self.tag('tbody')

    def body_content(self, items, **kwargs):
        for item in items:
            with self.row_tag(item=item, **kwargs):
                yield self.row_content(item=item, **kwargs)

    def foot_tag(self, **kwargs):
        return self.tag('tfoot')

    def foot_content(self, **kwargs):
        return
        yield

    def row_tag(self, **kwargs):
        return self.tag('tr')

    def row_content(self, **kwargs):
        for column in self.columns:
            with column.cell_tag(**kwargs):
                yield column.cell_content(**kwargs)

class Column(object):
    def __init__(self, label):
        self.label = label

    def setTable(self, table):
        self.tag = table.tag
        return self

    def head_tag(self, **kwargs):
        return self.tag('th')

    def head_content(self, **kwargs):
        yield self.label

    def cell_tag(self, **kwargs):
        return self.tag('td')

    def cell_content(self, item, **kwargs):
        yield str(item)

    def colspan(self):
        return 1


class SubjectTable(HtmlTable):
    def __init__(self, name, iconname):
        HtmlTable.__init__(self)
        self.name = name
        self.iconname = iconname

    def main(self, items, **kwargs):
        with self.tag('div', **{'class':['form-group']}):
            with self.tag('label', **{'class':['col-md-2', 'control-label']}):
                with self.tag('span', **{'class': ['text-nowrap']}):
                    with self.tag('i', **{'class':['fa', self.iconname], 'aria-hidden':'true'}):
                        pass
                    yield ' ' + self.name
                yield ':'
            with self.div_main_tag(items=items, **kwargs):
                yield self.div_main_content(items=items, **kwargs)

    def div_main_tag(self, **kwargs):
        return self.tag('div', **{'class':['col-md-10', 'metadata-append']})

    def table_tag(self, **kwargs):
        return HtmlTable.table_tag(self, **kwargs)\
            .set('data-paging', 'false')\
            .set('data-searching', 'false')\
            .append('class', 'table')\
            .append('class', 'data-list')

    def div_main_content(self, **kwargs):
        yield HtmlTable.main(self, **kwargs)

    def foot_tag(self, **kwargs):
        return self.tag(None)

class SubjectFormTable(SubjectTable):
    def __init__(self, action, **kwargs):
        SubjectTable.__init__(self, **kwargs)
        self.action = action

    def div_main_content(self, **kwargs):
        with self.form_tag(**kwargs):
            yield self.form_content(**kwargs)

    def form_tag(self, **kwargs):
        return self.tag('form', **{'action': self.action, 'role':'form', 'method':'POST'})

    def form_content(self, **kwargs):
        yield SubjectTable.div_main_content(self, **kwargs)

