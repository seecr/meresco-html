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

from meresco.components.http.utils import redirectHttp, notFoundHtml
from meresco.html import PostActions
from meresco.html.dynamichtml import escapeHtml
from urllib import urlencode
from urlparse import parse_qs

class UserGroupsForm(PostActions):
    def __init__(self, action, name=None, groupDescriptions=None):
        PostActions.__init__(self, name=name)
        self.registerAction('updateGroupsForUser', self.handleUpdateGroupsForUser)
        self._action = action
        self._groupDescriptions = groupDescriptions or {}

    def handleUpdateGroupsForUser(self, session=None, Body=None, **kwargs):
        user = session['user']
        if not user.isAdmin():
            yield notFoundHtml
            yield '<pre>Please go to the homepage and try again.</pre>'
            return
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        formUrl = bodyArgs['formUrl'][0]
        username = bodyArgs['username'][0]
        groupnames = set(bodyArgs.get('groupname', []))
        if username == user.name:
            groupnames.add('admin')
        self.do.setGroupsForUser(username=username, groupnames=groupnames)
        yield redirectHttp % formUrl

    def _describe(self, groupname):
        description = self._groupDescriptions.get(groupname)
        return '' if description is None else ' <em>(%s)</em>' % description

    def groupsForUser(self, username):
        return self.call.groupsForUser(username=username)

    def groupsUserForm(self, user, arguments, path, forUsername=None, **kwargs):
        if forUsername is None or not user.isAdmin():
            forUsername = user.name
        groupsForUser = self.call.groupsForUser(username=forUsername)
        formUrl = path
        if arguments:
            formUrl += "?" + urlencode(arguments, doseq=True)
        yield '<div id="usergroups-groups-user-form">'
        yield '<form name="groups" method="POST" action="{0}/updateGroupsForUser">'.format(self._action)
        yield '<input type="hidden" name="username" value="{0}"/>\n'.format(escapeHtml(forUsername))
        yield '<input type="hidden" name="formUrl" value="{0}"/>\n'.format(escapeHtml(formUrl))
        yield '<ul>'
        for groupname in sorted(self.call.listGroups()):
            yield '<li><label><input type="checkbox" name="groupname" value="{groupname}" {checked} {disabled}/>{groupname}{description}</label></li>'.format(
                    groupname=escapeHtml(groupname),
                    checked='checked="checked"' if groupname in groupsForUser else "",
                    disabled='disabled="disabled"' if groupname == 'admin' and forUsername == user.name else "",
                    description=self._describe(groupname)
                )
        yield '</ul>'
        yield '<input type="submit" value="Aanpassen"/>'
        yield '</form></div>'
