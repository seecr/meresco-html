## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2012 Meertens Instituut (KNAW) http://meertens.knaw.nl
# Copyright (C) 2012-2013 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Seecr Html"
# 
# "Seecr Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Seecr Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Seecr Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from meresco.core import Observable
from meresco.components.http.utils import CRLF, redirectHttp, okHtml
from cgi import parse_qs
from xml.sax.saxutils import quoteattr, escape as xmlEscape
from os.path import join, dirname
from securezone import ORIGINAL_PATH

class BasicHtmlLoginForm(Observable):
    def __init__(self, action, loginPath, home="/", name=None, userIsAdminMethod=None):
        Observable.__init__(self, name=name)
        self._action = action
        self._loginPath = loginPath
        self._home = home
        self._actions = {
            'changepassword': self.handleChangePassword,
            'remove': self.handleRemove,
            'newUser': self.handleNewUser,
        }
        self._userIsAdminMethod = userIsAdminMethod


    def handleRequest(self, Method, path, **kwargs):
        if Method == 'GET':
            yield redirectHttp % self._home
            return
        
        ignored, action = path.rsplit('/', 1)
        if action in self._actions:
            yield self._actions[action](path=path, **kwargs)
            return

        yield self.handleLogin(path=path, **kwargs)

    def handleLogin(self, session=None, Body=None, **kwargs):
        bodyArgs = parse_qs(Body, keep_blank_values=True)
        username = bodyArgs.get('username', [None])[0]
        password = bodyArgs.get('password', [None])[0]
        if self.call.validateUser(username=username, password=password):
            session['user'] = User(username, isAdminMethod=self._userIsAdminMethod)
            url = session.get(ORIGINAL_PATH, self._home)
            yield redirectHttp % url
        else:
            session['BasicHtmlLoginForm.formValues'] = {'username': username, 'errorMessage': 'Invalid username or password'}
            yield redirectHttp % self._loginPath

    def loginForm(self, session, path, **kwargs):
        formValues = session.get('BasicHtmlLoginForm.formValues', {}) if session else {}
        yield """<div id="login">\n"""
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])
        username = quoteattr(formValues.get('username', ''))
        action = quoteattr(self._action)
        formUrl = quoteattr(path)
        yield """    <form method="POST" name="login" action=%(action)s>
        <input type="hidden" name="formUrl" value=%(formUrl)s/>
        <dl>
            <dt>Username</dt>
            <dd><input type="text" name="username" value=%(username)s/></dd>
            <dt>Password</dt>
            <dd><input type="password" name="password"/></dd>
            <dd class="submit"><input type="submit" value="login"/></dd>
        </dl>
    </form>
</div>""" % locals()
        session.pop('BasicHtmlLoginForm.formValues', None)

    def newUserForm(self, session, path, **kwargs):
        formValues = session.get('BasicHtmlLoginForm.newUserFormValues', {}) if session else {}
        yield """<div id="login">\n"""
        if not 'user' in session:
            yield '<p class="error">Please login to add new users.</p>\n</div>'
            return
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])
        if 'successMessage' in formValues:
            yield '    <p class="success">%s</p>\n' % xmlEscape(formValues['successMessage'])
        username = quoteattr(formValues.get('username', ''))
        action = quoteattr(join(self._action, 'newUser'))
        formUrl = quoteattr(path)
        returnUrl = quoteattr(kwargs.get('returnUrl', path))
        yield """    <form method="POST" name="newUser" action=%(action)s>
        <input type="hidden" name="formUrl" value=%(formUrl)s/>
        <input type="hidden" name="returnUrl" value=%(returnUrl)s/>
        <dl>
            <dt>Username</dt>
            <dd><input type="text" name="username" value=%(username)s/></dd>
            <dt>Password</dt>
            <dd><input type="password" name="password"/></dd>
            <dt>Retype password</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="add"/></dd>
        </dl>
    </form>
</div>""" % locals()
        session.pop('BasicHtmlLoginForm.newUserFormValues', None)

    def handleNewUser(self, session, Body, **kwargs):
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        username = bodyArgs.get('username', [None])[0]
        password = bodyArgs.get('password', [None])[0]
        retypedPassword = bodyArgs.get('retypedPassword', [None])[0]
        formUrl = bodyArgs.get('formUrl', [self._home])[0]
        returnUrl = bodyArgs.get('returnUrl', [formUrl])[0]

        targetUrl = formUrl
        if password != retypedPassword:
            session['BasicHtmlLoginForm.newUserFormValues']={'username': username, 'errorMessage': 'Passwords do not match'}
        else:
            try:
                self.call.addUser(username=username, password=password)
                session['BasicHtmlLoginForm.newUserFormValues']={'successMessage': 'Added user "%s"' % username}
                targetUrl = returnUrl
            except ValueError, e:
                session['BasicHtmlLoginForm.newUserFormValues']={'username': username, 'errorMessage': str(e)}
        
        yield redirectHttp % targetUrl

    def handleChangePassword(self, session, Body, **kwargs):
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        username = bodyArgs.get('username', [None])[0]
        oldPassword = bodyArgs.get('oldPassword', [None])[0]
        newPassword = bodyArgs.get('newPassword', [None])[0]
        retypedPassword = bodyArgs.get('retypedPassword', [None])[0]
        formUrl = bodyArgs.get('formUrl', [self._home])[0]

        targetUrl = formUrl
        if newPassword != retypedPassword:
            session['BasicHtmlLoginForm.formValues']={'username': username, 'errorMessage': 'New passwords do not match'}
        else:
            if not self.call.validateUser(username=username, password=oldPassword):
                session['BasicHtmlLoginForm.formValues']={'username': username, 'errorMessage': 'Username and password do not match.'}
            else:
                self.call.changePassword(username, oldPassword, newPassword)
                targetUrl = self._home
        
        yield redirectHttp % targetUrl

    def changePasswordForm(self, session, path, **kwargs):
        formValues = session.get('BasicHtmlLoginForm.formValues', {}) if session else {}
        yield """<div id="login">\n"""
        if not 'user' in session:
            yield '<p class="error">Please login to change password.</p>\n</div>'
            return
        if 'errorMessage' in formValues:
            yield '    <p class="error">%s</p>\n' % xmlEscape(formValues['errorMessage'])
        yield """<form method="POST" name="changePassword" action=%s>
        <input type="hidden" name="formUrl" value=%s/>
        <input type="hidden" name="username" value=%s/>
        <dl>
            <dt>Old password</dt>
            <dd><input type="password" name="oldPassword"/></dd>
            <dt>New password</dt>
            <dd><input type="password" name="newPassword"/></dd>
            <dt>Retype new password</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="change"/></dd>
        </dl>
    </form>
</div>""" % (quoteattr(join(self._action, 'changepassword')), quoteattr(path), quoteattr(session['user'].name))
        session.pop('BasicHtmlLoginForm.formValues', None)

    def userList(self, session, path, **kwargs):
        yield """<div id="login">\n"""
        if not 'user' in session:
            yield '<p class="error">Please login to show user list.</p>\n</div>'
            return
        user = session['user']
        if user.isAdmin():
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
        yield '<ul>\n'
        for username in sorted(self.call.listUsernames()):
            yield '<li>%s' % xmlEscape(username)
            if user.isAdmin() and user.name != username:
                yield """ <a href="javascript:deleteUser('%s');">delete</a>""" % username
            yield '</li>\n'
        yield '</ul>\n'
        if user.isAdmin():
            yield '</form>\n'
        yield '</div>\n'

    def handleRemove(self, session, Body, **kwargs):
        bodyArgs = parse_qs(Body, keep_blank_values=True) if Body else {}
        formUrl = bodyArgs.get('formUrl', [self._home])[0]
        if 'user' in session and session['user'].isAdmin():
            username = bodyArgs.get('username', [None])[0]
            if self.call.hasUser(username):
                self.do.removeUser(username)
            else:
                session['BasicHtmlLoginForm.formValues'] = {
                    'errorMessage': 'User "%s" does not exist.' % username
                }

        yield redirectHttp % formUrl

class User(object):
    def __init__(self, name, isAdminMethod=None):
        self.name = name
        self._isAdmin = lambda name: name == 'admin' if isAdminMethod is None else isAdminMethod

    def isAdmin(self):
        return self._isAdmin(self.name)


