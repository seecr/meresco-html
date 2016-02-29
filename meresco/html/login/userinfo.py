## begin license ##
#
# "OBK-API" is a service for administrating SPARQL queries on the
# "Onderwijs Begrippenkader".
# "OBK-API" is developed for Stichting Kennisnet (http://kennisnet.nl)
# by Seecr (http://seecr.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com).
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
#
# This file is part of "OBK-API"
#
# "OBK-API" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "OBK-API" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "OBK-API"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components.json import JsonDict
from os.path import isfile

class UserInfo(object):
    version=1
    def __init__(self, filename):
        self._filename = filename
        self._info = {}
        if not isfile(self._filename):
            self._makePersistent()
        self._read()

    def enrichUser(self, user):
        self._loadUser(user)

    def addUserInfo(self, username, fullname):
        self._info[username] = {'fullname': fullname}
        self._makePersistent()

    def userInfo(self, username):
        return self._info.get(username, {})

    def _makePersistent(self):
        JsonDict(
                version=self.version,
                users=self._info,
            ).dump(self._filename)

    def _read(self):
        result = JsonDict.load(self._filename)
        assert result['version'] == self.version, 'Expected database version %s' % self.version
        self._info = result['users']

    def _loadUser(self, user):
        user.fullname = self.userInfo(user.name).get('fullname', '')
        user.title = lambda: user.fullname or user.name.title()
