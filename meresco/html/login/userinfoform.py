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

from meresco.components.http.utils import redirectHttp
from meresco.html import PostActions
from meresco.html.dynamichtml import escapeHtml
from urllib.parse import urlencode, parse_qs
from ._constants import UNAUTHORIZED

class UserInfoForm(PostActions):
    def __init__(self, action, name=None):
        PostActions.__init__(self, name=name)
        self.registerAction('updateInfoForUser', self.handleUpdateInfoForUser)
        self._action = action

    def handleUpdateInfoForUser(self, session, Body, **kwargs):
        handlingUser = session['user']
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        formUrl = bodyArgs['formUrl'][0]
        username = bodyArgs['username'][0]
        if not handlingUser.canEdit(username):
            yield UNAUTHORIZED
            return
        fullname = bodyArgs.get('fullname', [''])[0]
        self.do.addUserInfo(username=username, fullname=fullname)
        yield redirectHttp % formUrl

    def userInfoForm(self, user, forUsername, path, arguments, **kwargs):
        if not user.canEdit(forUsername):
            return
        formUrl = path
        if arguments:
            formUrl += "?" + urlencode(arguments, doseq=True)
        userinfo = self.call.userInfo(forUsername)
        yield '<div id="userinfoform-change-user-info">'
        yield '<form name="userinfo" method="POST" action="{0}/updateInfoForUser">'.format(self._action)
        yield '<input type="hidden" name="username" value="{0}"/>\n'.format(escapeHtml(forUsername))
        yield '<input type="hidden" name="formUrl" value="{0}"/>\n'.format(escapeHtml(formUrl))
        yield '<dl><dt>Volledige naam</dt><dd><input type="text" name="fullname" value="{0}"/></dd>\n'.format(escapeHtml(userinfo.get('fullname', '')))
        yield '<dt></dt><dd><input type="submit" value="Aanpassen"/></dd></dl>'
        yield '</form></div>'