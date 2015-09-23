## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase
from meresco.html.login import GroupsFile
from os.path import join

class GroupsFileTest(SeecrTestCase):
    def setUp(self):
        super(GroupsFileTest, self).setUp()
        self.groups = GroupsFile(join(self.tempdir, 'groups'), availableGroups=['users'])

    def testUserNoGroups(self):
        user = self.groups.userForName(username='username')
        self.assertEquals(set(), user.groups())

    def testListGroups(self):
        self.assertEquals(set(['admin', 'users']), self.groups.listGroups())

    def testAddUserToGroup(self):
        user = self.groups.userForName(username='username')
        self.assertEquals(set(), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin'])
        self.assertEquals(set(['admin']), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertEquals(set(['admin', 'users']), user.groups())

    def testAddUserOnlyToAvailableGroups(self):
        self.assertRaises(ValueError, lambda: self.groups.setGroupsForUser(username='username', groupnames=['newgroup']))

    def testIsAdmin(self):
        user = self.groups.userForName(username='username')
        self.assertFalse(user.isAdmin())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertTrue(user.isAdmin())
        self.groups.setGroupsForUser(username='username', groupnames=['users'])
        self.assertFalse(user.isAdmin())

    def testRemoveOldGroups(self):
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users', 'toberemoved'])
        gf.setGroupsForUser(username='test', groupnames=['users', 'toberemoved'])
        gf.setGroupsForUser(username='root', groupnames=['admin', 'users', 'toberemoved'])
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users'])
        self.assertEquals(set(['users', 'toberemoved']), gf.userForName('test').groups())
        self.assertEquals(set(['users', 'toberemoved', 'admin']), gf.userForName('root').groups())
        self.assertEquals(set(['users', 'toberemoved', 'admin']), gf.listGroups())
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users'], onlySpecifiedGroups=True)
        self.assertEquals(set(['users']), gf.userForName('test').groups())
        self.assertEquals(set(['users', 'admin']), gf.userForName('root').groups())
        self.assertEquals(set(['users', 'admin']), gf.listGroups())


    # def test



