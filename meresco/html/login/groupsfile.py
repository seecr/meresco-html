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
from simplejson import load as jsonRead, dump as jsonWrite
from os import rename, chmod
from stat import S_IRUSR, S_IWUSR
USER_RW = S_IRUSR | S_IWUSR

class GroupsFile(object):
    version=1
    def __init__(self, filename, availableGroups=None, onlySpecifiedGroups=False):
        self._filename = filename
        groups = set([] if availableGroups is None else availableGroups)
        groups.update(['admin'])
        self._groups = list(groups)
        self._users = {}
        if not isfile(filename):
            self._makePersistent()
            self._setGroupsForUser(username='admin', groupnames=['admin'])
        else:
            self._read()
        if onlySpecifiedGroups:
            for removedGroup in set(self._groups) - groups:
                for username, userGroups in self._users.items():
                    if removedGroup in userGroups:
                        self._setGroupsForUser(username=username, groupnames=(n for n in userGroups if n != removedGroup))
            self._groups = list(groups)
            self._makePersistent()

    def userForName(self, username):
        return self.User(username=username, db=self)

    def groupsForUser(self, username):
        return set(self._users.get(username, []))

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
        tmpFilename = self._filename + ".tmp"
        jsonWrite(dict(data=dict(users=self._users, groups=self._groups), version=self.version), open(tmpFilename, 'w'))
        rename(tmpFilename, self._filename)
        chmod(self._filename, USER_RW)

    def _read(self):
        result = jsonRead(open(self._filename))
        assert result['version'] == self.version, 'Expected database version %s' % self.version
        groups = set(self._groups)
        groups.update(set(result['data']['groups']))
        self._groups = list(groups)
        self._users.update(result['data']['users'])


    class User(object):
        def __init__(inner, username, db):
            inner.name = username
            inner._db = db

        def sortKey(inner):
            return inner.name

        def groups(inner):
            return inner._db.groupsForUser(username=inner.name)

        def isAdmin(inner):
            return 'admin' in inner.groups()
