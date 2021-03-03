## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2014-2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from meresco.components.http.utils import redirectHttp
from meresco.html import PostActions
from meresco.html.dynamichtml import escapeHtml
from urllib.parse import urlencode
from meresco.html.utils import parse_qs
from .groupsfile import GroupsFile
from ._constants import UNAUTHORIZED

class UserGroupsForm(PostActions):
    def __init__(self, action, name=None, groupDescriptions=None):
        PostActions.__init__(self, name=name)
        self.registerAction('updateGroupsForUser', self.handleUpdateGroupsForUser)
        self._action = action
        self._groupDescriptions = groupDescriptions or {}

    def handleUpdateGroupsForUser(self, session=None, Body=None, **kwargs):
        handlingUser = session['user']
        if not handlingUser.canEdit():
            yield UNAUTHORIZED
            return
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        formUrl = bodyArgs['formUrl'][0]
        username = bodyArgs['username'][0]
        groupnames = set(bodyArgs.get('groupname', []))

        if username == handlingUser.name:
            groupnames.update(handlingUser.managementGroups())
        else:
            oldGroupnames = self.groupsForUser(username)
            if GroupsFile.ADMIN in oldGroupnames and GroupsFile.ADMIN not in handlingUser.groups():
                yield UNAUTHORIZED
                return
        self.do.setGroupsForUser(username=username, groupnames=groupnames)
        yield redirectHttp % formUrl

    def handleNewUser(self, username, **kwargs):
        self.do.addUserToDefaultGroups(username)

    def _describe(self, groupname):
        description = self._groupDescriptions.get(groupname)
        return '' if description is None else ' <em>(%s)</em>' % description

    def groupsForUser(self, username):
        return self.call.groupsForUser(username=username)

    def groupsUserForm(self, user, arguments, path, forUsername=None, **kwargs):
        if not user.canEdit():
            return
        forUsername = user.name if forUsername is None else forUsername
        groupsInfo = self._groupsForForm(user=user, forUsername=forUsername)
        if not groupsInfo:
            return
        formUrl = path
        if arguments:
            formUrl += "?" + urlencode(arguments, doseq=True)
        yield '<div id="usergroups-groups-user-form">'
        yield '<form name="groups" method="POST" action="{0}/updateGroupsForUser">'.format(self._action)
        yield '<input type="hidden" name="username" value="{0}"/>\n'.format(escapeHtml(forUsername, quote=True))
        yield '<input type="hidden" name="formUrl" value="{0}"/>\n'.format(escapeHtml(formUrl, quote=True))
        yield '<ul>'
        for groupInfo in groupsInfo:
            yield '<li><label><input type="checkbox" name="groupname" value="{groupname}" {checked} {disabled}/>{groupname}{description}</label></li>'.format(
                    groupname=escapeHtml(groupInfo['groupname'], quote=True),
                    checked='checked="checked"' if groupInfo['checked'] else "",
                    disabled='disabled="disabled"' if groupInfo['disabled'] else "",
                    description=groupInfo['description'],
                )
        yield '</ul>'
        yield '<input type="submit" value="Aanpassen"/>'
        yield '</form></div>'

    def canEditGroups(self, user, forUsername):
        forUsername = user.name if forUsername is None else forUsername
        if not user.canEdit():
            return False
        groupsForUser = self.call.groupsForUser(username=forUsername)
        return GroupsFile.ADMIN in user.groups() or GroupsFile.ADMIN not in groupsForUser

    def _groupsForForm(self, user, forUsername):
        result = []
        groupsForUser = self.call.groupsForUser(username=forUsername)
        if GroupsFile.ADMIN in groupsForUser and not GroupsFile.ADMIN in user.groups():
            return result
        managingGroups = self.call.managingGroupsForUser(username=forUsername)
        for groupname in sorted(self.call.listGroups()):
            if user.name == forUsername:
                disabled = groupname == GroupsFile.ADMIN or groupname in managingGroups
            elif GroupsFile.ADMIN in user.groups():
                disabled = False
            else:
                disabled = groupname == GroupsFile.ADMIN
            result.append(dict(
                    groupname=groupname,
                    checked=groupname in groupsForUser,
                    disabled=disabled,
                    description=self._describe(groupname)
                ))
        return result
