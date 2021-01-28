## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2019-2021 SURF https://www.surf.nl
# Copyright (C) 2019-2021 Seecr (Seek You Too B.V.) https://seecr.nl
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
from meresco.html.errorlog import ErrorLog
from os import listdir
from os.path import join

class ErrorLogTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.log = ErrorLog(self.tempdir, logtofile=True, maxSize=10)

    def testRotate(self):
        for i in range(100):
            with open(join(self.tempdir, '{:03d}.error.txt'.format(i)), 'w') as f:
                f.write('')
        self.assertEqual(100, len(listdir(self.tempdir)))
        self.log.logError('Traceback', 'arg1', 'arg2', kwarg1='kwarg1', kwarg2='kwarg2')
        self.assertEqual(8, len(listdir(self.tempdir)))
        self.assertTrue('099.error.txt' in listdir(self.tempdir), listdir(self.tempdir))

