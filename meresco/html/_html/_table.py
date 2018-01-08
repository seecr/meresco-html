## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017-2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2018 SURF https://surf.nl
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

from ._html import Html
from .nextpreviterator import nextpreviterator

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
        for prevItem, item, nextItem in nextpreviterator(items):
            with self.row_tag(item=item, prevItem=prevItem, nextItem=nextItem, **kwargs):
                yield self.row_content(item=item, prevItem=prevItem, nextItem=nextItem, **kwargs)

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

