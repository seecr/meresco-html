## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2018 SURF https://surf.nl
# Copyright (C) 2018, 2020 Seecr (Seek You Too B.V.) http://seecr.nl
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

from unittest import TestCase

from meresco.html._html.nextpreviterator import nextpreviterator


class NextPrevIteratorTest(TestCase):
    def testNoIterator(self):
        self.assertRaises(TypeError, lambda: nextpreviterator(None))

    def testEmpty(self):
        self.assertEqual([], list(nextpreviterator([])))

    def testOneItem(self):
        self.assertEqual([(None, 1, None)], list(nextpreviterator([1])))

    def testTwoItems(self):
        self.assertEqual([(None, 1, 2), (1, 2, None)], list(nextpreviterator([1, 2])))

    def testMoreItems(self):
        self.assertEqual([(None,1,2), (1,2,3), (2,3,4), (3,4,5), (4,5,None)], list(nextpreviterator([1, 2, 3, 4, 5])))

