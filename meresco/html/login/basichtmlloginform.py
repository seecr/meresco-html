## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2012 Meertens Instituut (KNAW) http://meertens.knaw.nl
# Copyright (C) 2012-2018, 2020-2021, 2024 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
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

from meresco.components.http.utils import redirectHttp, CRLF, insertHeader, findCookies, okJson
from xml.sax.saxutils import quoteattr, escape as xmlEscape
from os.path import join
from .securezone import ORIGINAL_PATH
from simplejson import dumps, loads

from meresco.html import PostActions

from .labels import getLabel
from urllib.parse import urlencode
from meresco.html.utils import parse_qs
from time import time
from ._constants import UNAUTHORIZED

TWO_WEEKS = 2*7*24*3600

class BasicHtmlLoginForm(PostActions):
    def __init__(self, action, loginPath, home="/", name=None, lang='en', rememberMeCookie=False):
        PostActions.__init__(self, name=name)
        self._action = action
        self._loginPath = loginPath
        self._home = home
        self.registerAction('changepassword', self.handleChangePassword)
        self.registerAction('remove', self.handleRemove)
        self.registerAction('newUser', self.handleNewUser)
        self.defaultAction(self.handleLogin)
        self._lang = lang
        self._rememberMeCookie = rememberMeCookie

    def handleLogin(self, session=None, Body=None, **kwargs):
        accept = kwargs.get("Headers", {}).get("Accept", '')

        jsonResponse = 'application/json' in accept

        strBody = str(Body, encoding='utf-8')
        bodyArgs = {d['name']:[d['value']] for d in loads(strBody)} if jsonResponse else parse_qs(strBody, keep_blank_values=True)
        username = bodyArgs.get('username', [None])[0]
        password = bodyArgs.get('password', [None])[0]
        url = bodyArgs.get("redirect", [None])[0]
        rememberMe = bodyArgs.get('rememberMe', [None])[0] != None

        if self.call.validateUser(username=username, password=password):
            user = self.loginAsUser(username)
            session[USER] = user
            if url is None:
                url = session.pop(ORIGINAL_PATH, self._home)
            response = redirectHttp
            if rememberMe and self._rememberMeCookie:
                cookieValues = self.call.createCookie(user)
                status, headers = response.split(CRLF, 1)
                response = CRLF.join([status, cookieValues['header'], headers])
            if jsonResponse:
                yield bytes(okJson, encoding="utf-8")
                yield dumps(dict(success=True, url=url))
                return

            yield bytes(response % url, encoding='utf-8')
        else:
            session['BasicHtmlLoginForm.formValues'] = {
                'username': username,
                'errorMessage': getLabel(self._lang, 'loginForm', 'invalid')
            }
            if jsonResponse:
                yield bytes(okJson, encoding="utf-8")
                yield dumps(dict(success=False, message=getLabel(self._lang, 'loginForm', 'invalid')))
                return

            yield bytes(redirectHttp % self._loginPath, encoding='utf-8')

    def getUser(self, username):
        return self._checkAndCreateUser(username)
    loginAsUser = getUser

    def loginFormWithTag(self, session, path, lang=None, **kwargs):
        tag = kwargs.get('tag')
        formValues = session.get('BasicHtmlLoginForm.formValues', {}) if session else {}
        with tag("div", id_="login-form"):
            if "errorMessage" in formValues:
                with tag("p.error"):
                    yield formValues['errorMessage']
            with tag("form", method="POST", name="login", action=self._action):
                with tag("input", type_="hidden", name="formUrl", value=path): pass
                with tag("dl"):
                    with tag("dt"):
                        yield getLabel(lang, "loginForm", "username")
                    with tag("dd"):
                        with tag("input", type_="text", name="username", value=formValues.get("username")): pass
                    with tag("dt"):
                        yield getLabel(lang, "loginForm", "password")
                    with tag("dd"):
                        with tag("input", type_="password", name="password"): pass
                    if self._rememberMeCookie:
                        with tag("dt"):
                            yield tag.as_is("&nbsp;")
                        with tag("dd.rememberMe"):
                            with tag("input", type_="checkbox", name="rememberMe", id_="rememberMe"): pass
                            with tag("label", for_="rememberMe"):
                                yield getLabel(lang, 'loginForm', 'rememberMe')
                    with tag("dd.submit"):
                        with tag("input", type_="submit", id_="submitLogin", value=getLabel(lang, 'loginForm', "login")):
                            pass
                    with tag("script", type_="text/javascript"):
                        yield tag.as_is("document.getElementById('submitLogin').focus();")
        session.pop('BasicHtmlLoginForm.formValues', None)


    def loginForm(self, session, path, lang=None, withTag=False, **kwargs):
        lang = lang or self._lang
        if withTag:
            yield self.loginFormWithTag(session=session, path=path, lang=lang, **kwargs)
            return

        formValues = session.get('BasicHtmlLoginForm.formValues', {}) if session else {}
        yield """<div id="login-form">\n"""
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])

        values = dict(
            username=quoteattr(formValues.get('username', '')),
            action=quoteattr(self._action),
            formUrl=quoteattr(path),
            lblUsername=getLabel(lang, 'loginForm', 'username'),
            lblPassword=getLabel(lang, 'loginForm', 'password'),
            lblLogin=getLabel(lang, 'loginForm', 'login'),
            lblRememberMe=getLabel(lang, 'loginForm', 'rememberMe')
        )

        yield """
    <form method="POST" name="login" action=%(action)s>
        <input type="hidden" name="formUrl" value=%(formUrl)s/>
        <dl>
            <dt>%(lblUsername)s</dt>
            <dd><input type="text" name="username" value=%(username)s/></dd>
            <dt>%(lblPassword)s</dt>
            <dd><input type="password" name="password"/></dd>""" % values

        if self._rememberMeCookie:
            yield """
            <dt>&nbsp;</dt><dd class="rememberMe"><input type="checkbox" name="rememberMe" id="rememberMe" /><label for="rememberMe">%(lblRememberMe)s</label></dd>""" % values

        yield """
            <dd class="submit"><input type="submit" id="submitLogin" value="%(lblLogin)s"/></dd>
        </dl>
    </form>
    <script type="text/javascript">
        document.getElementById("submitLogin").focus()
    </script>
</div>""" % values
        session.pop('BasicHtmlLoginForm.formValues', None)

    def newUserForm(self, session, path, lang=None, extraFields="", **kwargs):
        lang = lang or self._lang
        formValues = session.get('BasicHtmlLoginForm.newUserFormValues', {}) if session else {}
        yield """<div id="login-new-user-form">\n"""
        if not USER in session:
            yield '<p class="error">Please login to add new users.</p>\n</div>'
            return
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])
        if 'successMessage' in formValues:
            yield '    <p class="success">%s</p>\n' % xmlEscape(formValues['successMessage'])

        values = dict(
            username=quoteattr(formValues.get('username', '')),
            action=quoteattr(join(self._action, 'newUser')),
            formUrl=quoteattr(path),
            returnUrl=quoteattr(kwargs.get('returnUrl', path)),
            lblUsername=getLabel(lang, 'newuserForm', 'username'),
            lblPassword=getLabel(lang, 'newuserForm', 'password'),
            lblPasswordRepeat=getLabel(lang, 'newuserForm', 'password-repeat'),
            lblCreate=getLabel(lang, 'newuserForm', 'create'),
            extraFields=extraFields
        )

        yield """
    <form method="POST" name="newUser" action=%(action)s>
        <input type="hidden" name="formUrl" value=%(formUrl)s/>
        <input type="hidden" name="returnUrl" value=%(returnUrl)s/>
        <dl>
            <dt>%(lblUsername)s</dt>
            <dd><input type="text" name="username" value=%(username)s/></dd>
            <dt>%(lblPassword)s</dt>
            <dd><input type="password" name="password"/></dd>
            <dt>%(lblPasswordRepeat)s</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            %(extraFields)s
            <dd class="submit"><input type="submit" value="%(lblCreate)s"/></dd>
        </dl>
    </form>
</div>""" % values
        session.pop('BasicHtmlLoginForm.newUserFormValues', None)

    def handleNewUser(self, session, Body, **kwargs):
        handlingUser = session.get(USER)
        if handlingUser is None or not handlingUser.canEdit():
            yield UNAUTHORIZED
            return
        bodyArgs = parse_qs(str(Body, encoding='utf-8'), keep_blank_values=True) if Body else {}
        username = bodyArgs.get('username', [None])[0]
        password = bodyArgs.get('password', [None])[0]
        retypedPassword = bodyArgs.get('retypedPassword', [None])[0]
        formUrl = bodyArgs.get('formUrl', [self._home])[0]
        returnUrl = bodyArgs.get('returnUrl', [formUrl])[0]
        targetUrl = formUrl
        if password != retypedPassword:
            session['BasicHtmlLoginForm.newUserFormValues']={'username': username, 'errorMessage': getLabel(self._lang, "newuserForm", 'dontMatch')}
        else:
            try:
                self.do.addUser(username=username, password=password)
                self.do.handleNewUser(username=username, Body=Body)
                session['BasicHtmlLoginForm.newUserFormValues']={'successMessage': '%s "%s"' % (getLabel(self._lang, 'newuserForm', 'added'), username)}
                targetUrl = returnUrl
            except ValueError as e:
                session['BasicHtmlLoginForm.newUserFormValues']={'username': username, 'errorMessage': str(e)}
        yield redirectHttp % targetUrl.format(username=username)

    def handleChangePassword(self, session, Body, **kwargs):
        bodyArgs = parse_qs(str(Body, encoding='utf-8'), keep_blank_values=True) if Body else {}
        username = bodyArgs.get('username', [None])[0]
        oldPassword = bodyArgs.get('oldPassword', [None])[0]
        newPassword = bodyArgs.get('newPassword', [None])[0]
        retypedPassword = bodyArgs.get('retypedPassword', [None])[0]
        formUrl = bodyArgs.get('formUrl', [self._home])[0]
        returnUrl = bodyArgs.get('returnUrl', [formUrl])[0]
        targetUrl = formUrl

        handlingUser = session.get(USER)
        if not handlingUser:
            session['BasicHtmlLoginForm.formValues']={
                'username': username,
                'errorMessage': getLabel(self._lang, 'changepasswordForm', 'loginRequired')}
            yield redirectHttp % targetUrl
            return

        if newPassword != retypedPassword:
            session['BasicHtmlLoginForm.formValues']={
                'username': username,
                'errorMessage': getLabel(self._lang, 'changepasswordForm', 'dontMatch')}
        else:
            if (not oldPassword and handlingUser.canEdit(username) and handlingUser.name != username) or self.call.validateUser(username=username, password=oldPassword):
                try:
                    self.call.setPassword(username, newPassword)
                    targetUrl = returnUrl
                    session['BasicHtmlLoginForm.formValues']={
                        'username': username,
                        'successMessage': getLabel(self._lang, 'changepasswordForm', 'passwordChanged')}
                except ValueError:
                    session['BasicHtmlLoginForm.formValues']={
                        'username': username,
                        'errorMessage': getLabel(self._lang, 'changepasswordForm', 'passwordInvalid')}

            else:
                session['BasicHtmlLoginForm.formValues']={
                    'username': username,
                    'errorMessage': getLabel(self._lang, 'changepasswordForm', 'usernamePasswordDontMatch')}
        yield redirectHttp % targetUrl.format(username=username)

    def changePasswordForm(self, session, path, arguments, user=None, lang=None, onlyNewPassword=False, **kwargs):
        lang = lang or self._lang
        formValues = session.get('BasicHtmlLoginForm.formValues', {}) if session else {}
        yield """<div id="login-change-password-form">\n"""
        if not USER in session:
            yield '<p class="error">Please login to change password.</p>\n</div>'
            return
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])

        formUrl = path
        if arguments:
            formUrl += "?" + urlencode(sorted(arguments.items()), doseq=True)

        username = session[USER].name if user is None else (user if isinstance(user, str) else user.name)
        values = dict(
            action=quoteattr(join(self._action, 'changepassword')),
            formUrl=quoteattr(formUrl),
            returnUrl=quoteattr(kwargs.get('returnUrl', path)),
            username=quoteattr(username),
            lblOldPassword=getLabel(lang, "changepasswordForm", "old-password"),
            lblNewPassword=getLabel(lang, "changepasswordForm", "new-password"),
            lblNewPasswordRepeat=getLabel(lang, "changepasswordForm", "new-password-repeat"),
            lblChange=getLabel(lang, "changepasswordForm", "change"),
        )

        yield """<form method="POST" name="changePassword" action=%(action)s>
        <input type="hidden" name="formUrl" value=%(formUrl)s/>
        <input type="hidden" name="returnUrl" value=%(returnUrl)s/>
        <input type="hidden" name="username" value=%(username)s/>
        <dl>
            """ % values
        if not onlyNewPassword:
            yield """<dt>%(lblOldPassword)s</dt>
            <dd><input type="password" name="oldPassword"/></dd>""" % values
        yield """
            <dt>%(lblNewPassword)s</dt>
            <dd><input type="password" name="newPassword"/></dd>
            <dt>%(lblNewPasswordRepeat)s</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="%(lblChange)s"/></dd>
        </dl>
    </form>
</div>""" % values
        session.pop('BasicHtmlLoginForm.formValues', None)

    def userList(self, session, path, userLink=None, **kwargs):
        yield """<div id="login-user-list">\n"""
        if not USER in session:
            yield '<p class="error">Please login to show user list.</p>\n</div>'
            return
        sessionUser = session[USER]
        if sessionUser.canEdit():
            yield """<script type="text/javascript">
function deleteUser(username) {
    if (confirm("Are you sure?")) {
        document.removeUser.username.value = username;
        document.removeUser.submit();
    }
}
            </script>"""
            yield """<form name="removeUser" method="POST" action=%s>
            <input type="hidden" name="formUrl" value=%s/>
            <input type="hidden" name="username"/>""" % (
                    quoteattr(join(self._action, 'remove')),
                    quoteattr(path),
                )
            yield '</form>\n'
        yield '<ul>\n'
        for user in sorted(self._listUsers(), key=lambda u:u.title()):
            yield '<li>'
            if userLink:
                yield '<a href="%s?user=%s">%s</a>' % (userLink, xmlEscape(user.name), xmlEscape(user.title()))
            else:
                yield xmlEscape(user.title())
            if sessionUser.name != user.name and (
                    sessionUser.canEdit(user.name)
                ):
                yield """ <a href="javascript:deleteUser('%s');">delete</a>""" % user.name
            yield '</li>\n'
        yield '</ul>\n'
        yield '</div>\n'

    def _sessionUserMayDeleteAUser(self, sessionUser, user):
        return user is not None and \
            sessionUser is not None and \
            sessionUser.name != user.name and \
            sessionUser.canEdit(user.name)

    def handleRemove(self, session, Body, **kwargs):
        bodyArgs = parse_qs(str(Body, encoding='utf-8'), keep_blank_values=True) if Body else {}
        formUrl = bodyArgs.get('formUrl', [self._home])[0]
        sessionUser = session.get(USER)
        user = self._checkAndCreateUser(bodyArgs.get('username', [None])[0])
        if not self._sessionUserMayDeleteAUser(sessionUser, user):
            yield UNAUTHORIZED
            return
        self.do.removeUser(user.name)
        self.do.removeCookies(filter=lambda anObject: anObject.name == user.name if isinstance(anObject, self.User) else False)
        self.do.removeCookies(filter=lambda anObject: anObject.get(USER).name == user.name if isinstance(anObject, dict) else False)
        yield redirectHttp % formUrl

    def logout(self, session, Headers, **ignored):
        session.pop(USER, None)
        redirectUrl = self._home
        response = redirectHttp % redirectUrl
        if not self._rememberMeCookie:
            yield response
            return
        cookieName = self.call.cookieName()
        for cookie in findCookies(Headers=Headers, name=cookieName):
            self.call.removeCookie(cookie)
        yield insertHeader([response], 'Set-Cookie: {}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/'.format(cookieName))

    def _listUsers(self):
        return [self._createUser(username) for username in self.call.listUsernames()]

    def _checkAndCreateUser(self, username):
        if not self.call.hasUser(username):
            return None
        return self._createUser(username)

    def _createUser(self, username):
        user = self.User(username)
        user.isValid = lambda: self.call.hasUser(username)
        self.do.enrichUser(user)
        return user

    def _now(self):
        return time()

    class User(object):
        def __init__(inner, name):
            inner.name = name

        def title(inner):
            return inner.name

        def isAdmin(inner):
            return inner.name == 'admin'

        def canEdit(inner, username=None):
            username = username.name if hasattr(username, 'name') else username
            return inner.isAdmin() or inner.name == username

USER = 'user'
