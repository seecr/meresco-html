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
        self.assertEqual(set(), user.groups())

    def testListGroups(self):
        self.assertEqual(set(['admin', 'management', 'users']), self.groups.listGroups())

    def testAddUserToGroup(self):
        user = BasicHtmlLoginForm.User('username')
        self.groups.enrichUser(user)
        self.assertEqual(set(), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin'])
        self.assertEqual(set(['admin']), user.groups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertEqual(set(['admin', 'users']), user.groups())

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
        self.assertEqual(set(), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['admin', 'users'])
        self.assertEqual(set(['admin']), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['management', 'users'])
        self.assertEqual(set(['management']), user.managementGroups())
        self.groups.setGroupsForUser(username='username', groupnames=['management', 'admin', 'users'])
        self.assertEqual(set(['admin', 'management']), user.managementGroups())

    def testRemoveOldGroups(self):
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users', 'toberemoved'])
        gf.setGroupsForUser(username='test', groupnames=['users', 'toberemoved'])
        gf.setGroupsForUser(username='root', groupnames=['admin', 'users', 'toberemoved'])
        gf = GroupsFile(join(self.tempdir, 'groups1'), availableGroups=['users'])
        usertest = BasicHtmlLoginForm.User('test')
        userroot = BasicHtmlLoginForm.User('root')
        gf.enrichUser(usertest)
        gf.enrichUser(userroot)
        self.assertEqual(set(['users', 'toberemoved']), usertest.groups())
        self.assertEqual(set(['users', 'toberemoved', 'admin']), userroot.groups())
        self.assertEqual(set(['users', 'toberemoved', 'admin']), gf.listGroups())
        gf.convert(keepOnlyTheseGroups=set(['users']))
        usertest = BasicHtmlLoginForm.User('test')
        userroot = BasicHtmlLoginForm.User('root')
        gf.enrichUser(usertest)
        gf.enrichUser(userroot)
        self.assertEqual(set(['users']), usertest.groups())
        self.assertEqual(set(['users', 'admin']), userroot.groups())
        self.assertEqual(set(['users', 'admin']), gf.listGroups())

    def testCanEdit(self):
        self.groups.setGroupsForUser('admin1', ['admin'])
        self.groups.setGroupsForUser('admin2', ['admin'])
        self.groups.setGroupsForUser('manager1', ['management'])
        self.groups.setGroupsForUser('manager2', ['management'])
        self.groups.setGroupsForUser('user1', ['users'])
        self.groups.setGroupsForUser('user2', ['users'])
        admin1 = BasicHtmlLoginForm.User('admin1')
        manager1 = BasicHtmlLoginForm.User('manager1')
        user1 = BasicHtmlLoginForm.User('user1')
        self.groups.enrichUser(admin1)
        self.groups.enrichUser(manager1)
        self.groups.enrichUser(user1)
        self.assertTrue(admin1.canEdit()) #any user
        self.assertTrue(admin1.canEdit('admin1'))
        self.assertTrue(admin1.canEdit(admin1))
        self.assertTrue(admin1.canEdit('manager1'))
        self.assertTrue(admin1.canEdit(manager1))
        self.assertTrue(admin1.canEdit('admin2'))
        self.assertTrue(admin1.canEdit('user1'))
        self.assertTrue(admin1.canEdit(user1))
        self.assertTrue(admin1.canEdit('unexisting'))
        self.assertTrue(manager1.canEdit())
        self.assertTrue(manager1.canEdit('manager1'))
        self.assertTrue(manager1.canEdit(manager1))
        self.assertTrue(manager1.canEdit('manager2'))
        self.assertFalse(manager1.canEdit('admin1'))
        self.assertFalse(manager1.canEdit(admin1))
        self.assertTrue(manager1.canEdit('user1'))
        self.assertTrue(manager1.canEdit('unexisting'))
        self.assertFalse(user1.canEdit())
        self.assertTrue(user1.canEdit('user1'))
        self.assertFalse(user1.canEdit('manager1'))
        self.assertFalse(user1.canEdit('admin1'))
        self.assertFalse(user1.canEdit('user2'))
        self.assertFalse(user1.canEdit('unexisting'))

    def testIsMember(self):
        self.groups.setGroupsForUser('user1', ['users', 'management'])
        class Group(object):
            def __init__(self, name):
                self.name = name
        users = Group('users')
        management = Group('management')
        others = Group('others')
        user1 = BasicHtmlLoginForm.User('user1')
        self.groups.enrichUser(user1)
        self.assertEqual(set(['users', 'management']), user1.groups())
        self.assertTrue(user1.isMemberOf('users'))
        self.assertTrue(user1.isMemberOf(users))
        self.assertTrue(user1.isMemberOfAny('users'))
        self.assertTrue(user1.isMemberOfAny(users))
        self.assertFalse(user1.isMemberOf('others'))
        self.assertFalse(user1.isMemberOf(others))
        self.assertFalse(user1.isMemberOfAny('others'))
        self.assertFalse(user1.isMemberOfAny(others))
        self.assertTrue(user1.isMemberOf('users', 'management'))
        self.assertTrue(user1.isMemberOf(users, management))
        self.assertTrue(user1.isMemberOfAny('users', 'management'))
        self.assertTrue(user1.isMemberOfAny(users, management))
        self.assertFalse(user1.isMemberOf('users', 'others'))
        self.assertFalse(user1.isMemberOf(users, others))
        self.assertTrue(user1.isMemberOfAny('users', 'others'))
        self.assertTrue(user1.isMemberOfAny(users, others))
        self.assertRaises(ValueError, lambda: user1.isMemberOf())
        self.assertRaises(ValueError, lambda: user1.isMemberOfAny())

