## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2014-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
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
from weightless.core import asString
from meresco.html.login import GroupsFile, UserGroupsForm, BasicHtmlLoginForm
from os.path import join
from urllib.parse import urlencode

class UserGroupsFormTest(SeecrTestCase):
    def setUp(self):
        super(UserGroupsFormTest, self).setUp()
        self.groupsFile = GroupsFile(filename=join(self.tempdir, 'groups'), availableGroups=['admin', 'users', 'special', 'management'], groupsForUserManagement=['management'], defaultGroups=['users'])
        self.userGroups = UserGroupsForm(action='/action')
        self.userGroups.addObserver(self.groupsFile)
        self.groupsFile.setGroupsForUser(username='normal', groupnames=['users'])
        self.groupsFile.setGroupsForUser(username='bob', groupnames=['admin', 'users'])
        self.groupsFile.setGroupsForUser(username='bill', groupnames=['management'])
        self.otherManagerName = 'tim'
        self.otherAdminName = 'johan'
        self.groupsFile.setGroupsForUser(username=self.otherManagerName, groupnames=['management'])
        self.groupsFile.setGroupsForUser(username=self.otherAdminName, groupnames=['admin'])
        self.normalUser = BasicHtmlLoginForm.User('normal')
        self.adminUser = BasicHtmlLoginForm.User('bob')
        self.managementUser = BasicHtmlLoginForm.User('bill')
        self.groupsFile.enrichUser(self.normalUser)
        self.groupsFile.enrichUser(self.adminUser)
        self.groupsFile.enrichUser(self.managementUser)

    def testSetup(self):
        self.assertEqual(set(['admin', 'users']), self.adminUser.groups())
        self.assertFalse(self.normalUser.canEdit())
        self.assertTrue(self.adminUser.canEdit())
        self.assertTrue(self.managementUser.canEdit())

    def testHandleUpdateGroupsForUser(self):
        Body = urlencode({'username': [self.adminUser.name], 'groupname': ['special'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.adminUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /useraccount\r\n\r\n', result)
        self.assertEqual(set(['admin', 'special']), self.adminUser.groups())

    def testHandleUpdateGroupsForManagementUser(self):
        Body = urlencode({'username': [self.managementUser.name], 'groupname': ['special'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.managementUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /useraccount\r\n\r\n', result)
        self.assertEqual(set(['management', 'special']), self.managementUser.groups())

    def testHandleUpdateGroupsForUser_if_not_admin(self):
        Body = urlencode({'username': [self.adminUser.name], 'groupname': ['special'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.normalUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 401 Unauthorized', result.split('\r\n')[0])

    def testAdminChangesManagement(self):
        self.assertEqual(set(['management']), self.managementUser.groups())
        self.assertEqual(set(['admin', 'users']), self.adminUser.groups())

        Body = urlencode({'username': [self.managementUser.name], 'groupname': ['special', 'users'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.adminUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /useraccount\r\n\r\n', result)

        self.assertEqual(set(['special', 'users']), self.managementUser.groups())
        self.assertEqual(set(['admin', 'users']), self.adminUser.groups())

    def testManagementChangesNormalUserGroups(self):
        self.assertEqual(set(['users']), self.normalUser.groups())
        self.assertEqual(set(['management']), self.managementUser.groups())

        Body = urlencode({'username': [self.normalUser.name], 'groupname': ['special'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.managementUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /useraccount\r\n\r\n', result)

        self.assertEqual(set(['special']), self.normalUser.groups())
        self.assertEqual(set(['management']), self.managementUser.groups())

    def testManagementCannotChangeAdminUser(self):
        self.assertEqual(set(['admin', 'users']), self.adminUser.groups())
        self.assertEqual(set(['management']), self.managementUser.groups())

        Body = urlencode({'username': [self.adminUser.name], 'groupname': ['special', 'users'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.managementUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 401 Unauthorized', result.split('\r\n')[0])

        self.assertEqual(set(['management']), self.managementUser.groups())
        self.assertEqual(set(['admin', 'users']), self.adminUser.groups())

    def testAdminCanChangeOtherAdmins(self):
        otherAdminUser = BasicHtmlLoginForm.User('johan')
        self.groupsFile.enrichUser(otherAdminUser)

        Body = urlencode({'username': [otherAdminUser.name], 'groupname': ['special'], 'formUrl': ['/useraccount']}, doseq=True)
        session = {'user':self.adminUser}
        result = asString(self.userGroups.handleRequest(Method='POST', path='/action/updateGroupsForUser', session=session, Body=Body))
        self.assertEqual('HTTP/1.0 302 Found\r\nLocation: /useraccount\r\n\r\n', result)

        self.assertEqual(set(['special']), otherAdminUser.groups())

    def testGroupsUserFormAdminSelf(self):
        kwargs = {
            'path': '/path/to/form',
            'arguments': {'key': ['value']},
        }
        self.assertEqualsWS("""<div id="usergroups-groups-user-form">
    <form name="groups" method="POST" action="/action/updateGroupsForUser">
        <input type="hidden" name="username" value="bob"/>
        <input type="hidden" name="formUrl" value="/path/to/form?key=value"/>
        <ul>
            <li><label><input type="checkbox" name="groupname" value="admin" checked="checked" disabled="disabled"/>admin</label></li>
            <li><label><input type="checkbox" name="groupname" value="management"  />management</label></li>
            <li><label><input type="checkbox" name="groupname" value="special"  />special</label></li>
            <li><label><input type="checkbox" name="groupname" value="users" checked="checked" />users</label></li>
        </ul>
        <input type="submit" value="Aanpassen"/>
    </form>
</div>""", asString(self.userGroups.groupsUserForm(user=self.adminUser, **kwargs)))
        self.assertEqual([
            dict(checked=True,  description='', disabled=True,  groupname='admin'),
            dict(checked=False, description='', disabled=False, groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=True,  description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.adminUser, forUsername=self.adminUser.name))
        self.assertTrue(self.userGroups.canEditGroups(user=self.adminUser, forUsername=self.adminUser.name))

    def testGroupsUserFormManagementSelf(self):
        self.assertEqual([
            dict(checked=False, description='', disabled=True,  groupname='admin'),
            dict(checked=True,  description='', disabled=True,  groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=False, description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.managementUser, forUsername=self.managementUser.name))
        self.assertTrue(self.userGroups.canEditGroups(user=self.managementUser, forUsername=self.managementUser.name))

    def testGroupsUserFormManagementOtherManager(self):
        self.assertEqual([
            dict(checked=False, description='', disabled=True,  groupname='admin'),
            dict(checked=True,  description='', disabled=False, groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=False, description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.managementUser, forUsername=self.otherManagerName))
        self.assertTrue(self.userGroups.canEditGroups(user=self.managementUser, forUsername=self.otherManagerName))

    def testGroupsUserFormManagementOtherUser(self):
        self.assertEqual([
            dict(checked=False, description='', disabled=True,  groupname='admin'),
            dict(checked=False, description='', disabled=False, groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=True,  description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.managementUser, forUsername=self.normalUser.name))
        self.assertTrue(self.userGroups.canEditGroups(user=self.managementUser, forUsername=self.normalUser.name))

    def testGroupsUserFormManagementAdmin(self):
        kwargs = {
            'path': '/path/to/form',
            'arguments': {'key': ['value']},
        }
        self.assertEqual('', asString(self.userGroups.groupsUserForm(user=self.managementUser, forUsername=self.adminUser.name, **kwargs)))
        self.assertFalse(self.userGroups.canEditGroups(user=self.managementUser, forUsername=self.adminUser.name))
        self.assertEqual([], self.userGroups._groupsForForm(user=self.managementUser, forUsername=self.adminUser.name))

    def testGroupsUserFormUser(self):
        kwargs = {
            'path': '/path/to/form',
            'arguments': {'key': ['value']},
        }
        self.assertEqual('', asString(self.userGroups.groupsUserForm(user=self.normalUser, **kwargs)))
        self.assertFalse(self.userGroups.canEditGroups(user=self.normalUser, forUsername=self.normalUser.name))

    def testGroupsUserFormAdminOtherAdmin(self):
        self.assertEqual([
            dict(checked=True,  description='', disabled=False, groupname='admin'),
            dict(checked=False, description='', disabled=False, groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=False, description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.adminUser, forUsername=self.otherAdminName))
        self.assertTrue(self.userGroups.canEditGroups(user=self.adminUser, forUsername=self.otherAdminName))

    def testGroupsUserFormAdminManager(self):
        self.assertEqual([
            dict(checked=False, description='', disabled=False, groupname='admin'),
            dict(checked=True,  description='', disabled=False, groupname='management'),
            dict(checked=False, description='', disabled=False, groupname='special'),
            dict(checked=False, description='', disabled=False, groupname='users'),
            ], self.userGroups._groupsForForm(user=self.adminUser, forUsername=self.otherManagerName))
        self.assertTrue(self.userGroups.canEditGroups(user=self.adminUser, forUsername=self.otherManagerName))

    def testHandleNewUser(self):
        self.userGroups.handleNewUser(username='johan', Body="ignored")
        self.assertEqual(set(['users']), self.groupsFile.groupsForUser('johan'))