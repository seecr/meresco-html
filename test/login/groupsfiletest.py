## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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
from meresco.html.login import GroupsFile, BasicHtmlLoginForm
from os.path import join

class GroupsFileTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.groups = GroupsFile(join(self.tempdir, 'groups'), availableGroups=['users'], groupsForUserManagement=['management'])

    def testUserNoGroups(self):
        user = BasicHtmlLoginForm.User('username')
        self.groups.enrichUser(user)
        self.assertEquals(set(), user.groups())

    def testListGroups(self):
        self.assertEquals(set(['admin', 'management', 'users']), self.groups.listGroups())

    def testAddUserToGroup(self):
        user = BasicHtmlLoginForm.User('username')
        self.groups.enrichUser(user)
        self.assertEquals(set(), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin'])
        self.assertEquals(set(['admin']), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertEquals(set(['admin', 'users']), user.groups())

    def testAddUserOnlyToAvailableGroups(self):
        self.assertRaises(ValueError, lambda: self.groups.setGroupsForUser(username='username', groupnames=['newgroup']))

    def testIsAdmin(self):
        user = BasicHtmlLoginForm.User('username')
        self.groups.enrichUser(user)
        self.assertFalse(user.isAdmin())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertTrue(user.isAdmin())
        self.groups.setGroupsForUser(username='username', groupnames=['users'])
        self.assertFalse(user.isAdmin())
        self.groups.setGroupsForUser(username='username', groupnames=['users', 'management'])
        self.assertFalse(user.isAdmin())

    def testManagementGroups(self):
        user = BasicHtmlLoginForm.User('username')
        self.groups.enrichUser(user)
        self.assertEquals(set(), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertEquals(set(['admin']), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['management', 'users'])
        self.assertEquals(set(['management']), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['management', 'admin', 'users'])
        self.assertEquals(set(['admin', 'management']), user.managementGroups())

    def testRemoveOldGroups(self):
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users', 'toberemoved'])
        gf.setGroupsForUser(username='test', groupnames=['users', 'toberemoved'])
        gf.setGroupsForUser(username='root', groupnames=['admin', 'users', 'toberemoved'])
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users'])
        usertest = BasicHtmlLoginForm.User('test')
        userroot = BasicHtmlLoginForm.User('root')
        gf.enrichUser(usertest)
        gf.enrichUser(userroot)
        self.assertEquals(set(['users', 'toberemoved']), usertest.groups())
        self.assertEquals(set(['users', 'toberemoved', 'admin']), userroot.groups())
        self.assertEquals(set(['users', 'toberemoved', 'admin']), gf.listGroups())
        gf.convert(keepOnlyTheseGroups=set(['users']))
        usertest = BasicHtmlLoginForm.User('test')
        userroot = BasicHtmlLoginForm.User('root')
        gf.enrichUser(usertest)
        gf.enrichUser(userroot)
        self.assertEquals(set(['users']), usertest.groups())
        self.assertEquals(set(['users', 'admin']), userroot.groups())
        self.assertEquals(set(['users', 'admin']), gf.listGroups())

    def testCanEdit(self):
        self.groups.setGroupsForUser('admin1', ['admin'])
        self.groups.setGroupsForUser('admin2', ['admin'])
        self.groups.setGroupsForUser('manager1', ['management'])
        self.groups.setGroupsForUser('manager2', ['management'])
        self.groups.setGroupsForUser('user1', ['users'])
        self.groups.setGroupsForUser('user2', ['users'])
        admin = BasicHtmlLoginForm.User('admin1')
        manager = BasicHtmlLoginForm.User('manager1')
        user = BasicHtmlLoginForm.User('user1')
        self.groups.enrichUser(admin)
        self.groups.enrichUser(manager)
        self.groups.enrichUser(user)
        self.assertTrue(admin.canEdit()) #any user
        self.assertTrue(admin.canEdit('admin1'))
        self.assertTrue(admin.canEdit('manager1'))
        self.assertTrue(admin.canEdit('admin2'))
        self.assertTrue(admin.canEdit('user1'))
        self.assertTrue(admin.canEdit('unexisting'))
        self.assertTrue(manager.canEdit())
        self.assertTrue(manager.canEdit('manager1'))
        self.assertTrue(manager.canEdit('manager2'))
        self.assertFalse(manager.canEdit('admin1'))
        self.assertTrue(manager.canEdit('user1'))
        self.assertTrue(manager.canEdit('unexisting'))
        self.assertFalse(user.canEdit())
        self.assertTrue(user.canEdit('user1'))
        self.assertFalse(user.canEdit('manager1'))
        self.assertFalse(user.canEdit('admin1'))
        self.assertFalse(user.canEdit('user2'))
        self.assertFalse(user.canEdit('unexisting'))

    # def testCanEditGroup(self):
    #     self.groups.setGroupsForUser('admin1', ['admin'])
    #     self.groups.setGroupsForUser('admin2', ['admin'])
    #     self.groups.setGroupsForUser('manager1', ['management'])
    #     self.groups.setGroupsForUser('manager2', ['management'])
    #     self.groups.setGroupsForUser('user1', ['users'])
    #     self.groups.setGroupsForUser('user2', ['users'])
    #     admin = BasicHtmlLoginForm.User('admin1')
    #     manager = BasicHtmlLoginForm.User('manager1')
    #     user = BasicHtmlLoginForm.User('user1')
    #     self.groups.enrichUser(admin)
    #     self.groups.enrichUser(manager)
    #     self.groups.enrichUser(user)
    #     self.assertTrue(admin.canEditGroup())
    #     self.assertTrue(admin.canEditGroup('admin1'))
    #     self.assertTrue(admin.canEditGroup('manager1'))
    #     self.assertTrue(admin.canEditGroup('admin2'))
    #     self.assertTrue(admin.canEditGroup('user1'))
    #     self.assertTrue(manager.canEditGroup())
    #     self.assertTrue(manager.canEditGroup('manager1'))
    #     self.assertTrue(manager.canEditGroup('manager2'))
    #     self.assertFalse(manager.canEditGroup('admin1'))
    #     self.assertTrue(manager.canEditGroup('user1'))
    #     self.assertFalse(user.canEditGroup())
    #     self.assertFalse(user.canEditGroup('user1'))
    #     self.assertFalse(user.canEditGroup('manager1'))
    #     self.assertFalse(user.canEditGroup('admin1'))
    #     self.assertFalse(user.canEditGroup('user2'))

