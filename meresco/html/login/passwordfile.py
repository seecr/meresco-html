## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2012 Meertens Instituut (KNAW) http://meertens.knaw.nl
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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
from hashlib import md5
from stat import S_IRUSR, S_IWUSR
from re import compile as reCompile
from random import choice
from string import digits as _SALT_1, ascii_letters as _SALT_2
from meresco.components.json import JsonDict

USER_RW = S_IRUSR | S_IWUSR

def md5Hash(data):
    return md5(data.encode()).hexdigest()

def simplePasswordTest(passwd):
    return bool(passwd.strip())

VALIDNAME=reCompile(r'^[\w@\-\.]+$')
def usernameTest(username):
    return bool(VALIDNAME.match(username))

def randomString(length=5):
    return ''.join(choice(_SALT_1 + _SALT_2) for i in range(length))

class PasswordFile(object):
    version=2

    def __init__(self,
            filename,
            hashMethod=md5Hash,
            passwordTest=simplePasswordTest,
            usernameTest=usernameTest):
        self._hashMethod = hashMethod
        self._passwordTest = passwordTest
        self._usernameTest = usernameTest
        self._filename = filename
        self._users = {}
        if not isfile(filename):
            self._makePersistent()
            self._setUser('admin', 'admin')
        else:
            self._users.update(self._read())

    def addUser(self, username, password):
        if not self._usernameTest(username):
            raise ValueError('Invalid username.')
        if username in self._users:
            raise ValueError('User already exists.')
        self._setUser(username=username, password=password)

    def removeUser(self, username):
        del self._users[username]
        self._makePersistent()

    def validateUser(self, username, password):
        valid = False
        try:
            user = self._users[username]
            valid = user['password'] == self._hashMethod(password + user['salt'])
            if valid and not user['salt']:
                self._setUser(username=username, password=password)
        except KeyError:
            pass
        return valid

    def changePassword(self, username, oldPassword, newPassword):
        if oldPassword and not self.validateUser(username=username, password=oldPassword):
            raise ValueError('Username and password do not match, password NOT changed.')
        self._setUser(username=username, password=newPassword)

    def listUsernames(self):
        return list(self._users.keys())

    def hasUser(self, username):
        return username in self._users

    @classmethod
    def convert(cls, src, dst):
        users = dict()
        with open(src) as i:
            for user, pwhash in (l.strip().split(':') for l in i if ':' in l.strip()):
                users[user]=dict(salt='', password=pwhash)
        JsonDict(users=users, version=cls.version).dump(dst)
        return cls(dst)

    def _makePersistent(self):
        JsonDict(users=self._users, version=self.version).dump(self._filename)
        chmod(self._filename, USER_RW)

    def _read(self):
        result = JsonDict.load(self._filename)
        assert result['version'] == self.version, 'Expected database version %s' % self.version
        return result['users']

    def _setUser(self, username, password):
        if not self._passwordTest(password):
            raise ValueError('Invalid password.')
        salt = randomString()
        self._users[username] = dict(salt=salt, password=self._hashMethod(password + salt))
        self._makePersistent()

