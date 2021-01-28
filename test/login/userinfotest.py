## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
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
from os.path import join
from meresco.html.login import BasicHtmlLoginForm, UserInfo

User = BasicHtmlLoginForm.User

class UserInfoTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.userinfo = UserInfo(join(self.tempdir, 'userinfo'))

    def testFullname(self):
        self.userinfo.addUserInfo('username', fullname='Full Username')
        user = User('username')
        self.userinfo.enrichUser(user)
        self.assertEqual('Full Username', user.fullname)
        self.assertEqual('Full Username', user.title())

    def testFullnameAfterChange(self):
        self.userinfo.addUserInfo('username', fullname='Full Username')
        self.userinfo.addUserInfo('username2', fullname='Full Username 2')
        user = User('username')
        user2 = User('username2')
        self.userinfo.enrichUser(user)
        self.assertEqual('Full Username', user.fullname)
        self.userinfo.addUserInfo('username', fullname='New Fullname')
        self.assertEqual('New Fullname', user.fullname)
        self.assertEqual('Full Username 2', user2.fullname)
        self.assertEqual('New Fullname', user.title())

    def testFullnameIfNotSet(self):
        user = User('username')
        self.userinfo.enrichUser(user)
        self.assertEqual('', user.fullname)
        self.assertEqual('Username', user.title())

    def testPersistent(self):
        self.userinfo.addUserInfo('username', fullname='Full Username')
        self.assertEqual('Full Username', UserInfo(join(self.tempdir, 'userinfo')).userInfo('username')['fullname'])
