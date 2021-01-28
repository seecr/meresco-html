## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2016, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2016, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
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
from seecr.test.utils import headerToDict
from meresco.components.http.utils import CRLF
from meresco.html.login import UserInfo, UserInfoForm
from meresco.html.login import BasicHtmlLoginForm
from os.path import join
from weightless.core import asString
from urllib.parse import urlencode

class UserInfoFormTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.info = UserInfo(join(self.tempdir, 'users'))
        self.form = UserInfoForm(action='/action')
        self.form.addObserver(self.info)
        self.info.addUserInfo('normal', fullname='Full Username')
        self.adminUser = BasicHtmlLoginForm.User('admin')
        self.normalUser = BasicHtmlLoginForm.User('normal')

    def testSetup(self):
        self.assertTrue(self.adminUser.canEdit('normal'))
        self.assertFalse(self.normalUser.canEdit('admin'))

    def testUpdateInfoForUser(self):
        data = {
            'formUrl': ['/user'],
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.adminUser}))
        self.assertEqual('HTTP/1.0 302 Found', result.split(CRLF)[0])
        self.assertEqual({'Location': '/user'}, headerToDict(result))
        self.assertEqual({'fullname': 'THE user'}, self.info.userInfo('aUser'))

    def testUpdateUserByOtherUserFails(self):
        data = {
            'formUrl': ['/user'],
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.normalUser}))
        self.assertEqual('HTTP/1.0 401 Unauthorized', result.split(CRLF)[0])
        self.assertEqual({}, self.info.userInfo('aUser'))

    def testUpdateInfoForUserByItself(self):
        data = {
            'formUrl': ['/user'],
            'username': [self.normalUser.name],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.normalUser}))
        self.assertEqual('HTTP/1.0 302 Found', result.split(CRLF)[0])
        self.assertEqual({'Location': '/user'}, headerToDict(result))
        self.assertEqual({'fullname': 'THE user'}, self.info.userInfo(self.normalUser.name))

    def testForm(self):
        result = asString(self.form.userInfoForm(self.normalUser, forUsername=self.normalUser.name, path='/path/to/form', arguments={'key':['value']}))
        self.assertEqualsWS('''<div id="userinfoform-change-user-info">
<form name="userinfo" method="POST" action="/action/updateInfoForUser">
<input type="hidden" name="username" value="normal"/>
<input type="hidden" name="formUrl" value="/path/to/form?key=value"/>
<dl>
    <dt>Volledige naam</dt>
    <dd><input type="text" name="fullname" value="Full Username"/></dd>
    <dt></dt>
    <dd><input type="submit" value="Aanpassen"/></dd>
</dl>
</form>
</div>''', result)

    def testFormNormalUserOfOtherUser(self):
        result = asString(self.form.userInfoForm(self.normalUser, forUsername='other', path='/path/to/form', arguments={'key':['value']}))
        self.assertEqual('', result)

    def testHandleNewUser(self):
        data = {
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        self.form.handleNewUser(username='user', Body=urlencode(data, doseq=True))
        self.assertEqual({'fullname': 'THE user'}, self.info.userInfo('user'))