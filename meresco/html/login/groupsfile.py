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

from os.path import isfile
from os import chmod
from stat import S_IRUSR, S_IWUSR
from meresco.components.json import JsonDict

USER_RW = S_IRUSR | S_IWUSR

class GroupsFile(object):
    version=1
    ADMIN = 'admin'
    def __init__(self, filename, availableGroups=None, groupsForUserManagement=None):
        self._filename = filename
        self._groupsForUserManagement = set([]) if groupsForUserManagement is None else set(groupsForUserManagement)
        self._groupsForUserManagement.add(self.ADMIN)
        groups = set([] if availableGroups is None else availableGroups)
        groups.update(self._groupsForUserManagement)
        self._groups = list(groups)
        self._users = {}
        if not isfile(filename):
            self._makePersistent()
            self._setGroupsForUser(username='admin', groupnames=[self.ADMIN])
        else:
            self._read()

    def enrichUser(self, user):
        user.groups = lambda: self.groupsForUser(username=user.name)
        user.isAdmin = lambda: self.ADMIN in user.groups()
        user.canEdit = lambda username=None: self._canEdit(user, username)
        user.managementGroups = lambda: self.managingGroupsForUser(user.name)
        user.isMemberOf = lambda *groups: self._userMemberOf(user, *groups, memberOfAll=True)
        user.isMemberOfAny = lambda *groups: self._userMemberOf(user, *groups, memberOfAll=False)

    def _canEdit(self, user, username=None):
        username = username.name if hasattr(username, 'name') else username
        return user.isAdmin() or \
                user.name == username or \
                self._groupsForUserManagement.intersection(user.groups()) and \
                self.ADMIN not in self.groupsForUser(username)

    def _userMemberOf(self, user, *groups, **kwargs):
        if not groups:
            raise ValueError('No groups specified')
        memberOfAll = kwargs.get('memberOfAll', True)
        groups = set(g.name if hasattr(g, 'name') else g for g in groups)
        both = self.groupsForUser(user.name).intersection(groups)
        if memberOfAll:
            return len(both) == len(groups)
        return bool(both)

    def groupsForUser(self, username):
        return set(self._users.get(username, []))

    def removeUser(self, username):
        self._users.pop(username, None)
        self._makePersistent()

    def managingGroupsForUser(self, username):
        return self.groupsForUser(username).intersection(self._groupsForUserManagement)

    def listGroups(self, used=False):
        if used:
            return set(groupname for groups in self._users.values() for groupname in groups)
        return set(self._groups)

    def setGroupsForUser(self, username, groupnames):
        if not set(groupnames).issubset(set(self._groups)):
            raise ValueError("The groups: {0} cannot be used.".format(list(set(groupnames)-set(self._groups))))
        self._setGroupsForUser(username=username, groupnames=groupnames)

    def _setGroupsForUser(self, username, groupnames):
        self._users[username] = list(set(groupnames))
        self._makePersistent()

    def _makePersistent(self):
        JsonDict(data=dict(users=self._users, groups=self._groups), version=self.version).dump(self._filename)
        chmod(self._filename, USER_RW)

    def _read(self):
        result = JsonDict.load(self._filename)
        assert result['version'] == self.version, 'Expected database version %s' % self.version
        groups = set(self._groups)
        groups.update(set(result['data']['groups']))
        self._groups = list(groups)
        self._users.update(result['data']['users'])

    def convert(self, keepOnlyTheseGroups):
        keepOnlyTheseGroups = set(keepOnlyTheseGroups)
        keepOnlyTheseGroups.update(self._groupsForUserManagement)
        for removedGroup in set(self._groups) - keepOnlyTheseGroups:
            for username, userGroups in self._users.items():
                if removedGroup in userGroups:
                    self._setGroupsForUser(username=username, groupnames=(n for n in userGroups if n != removedGroup))
        self._groups = list(keepOnlyTheseGroups)
        self._makePersistent()


