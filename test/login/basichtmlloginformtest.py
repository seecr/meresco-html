## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2012 Meertens Instituut (KNAW) http://meertens.knaw.nl
# Copyright (C) 2012-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from weightless.core import asString, be, Observable, consume

from seecr.test import SeecrTestCase, CallTrace
from meresco.components.http.utils import CRLF
from urllib import urlencode

from seecr.html.login import BasicHtmlLoginForm, PasswordFile
from seecr.html.login.basichtmlloginform import User
from seecr.html.login.securezone import ORIGINAL_PATH
from os.path import join

class BasicHtmlLoginFormTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.form = BasicHtmlLoginForm(action='/action', loginPath='/login', home='/home')

    def testLoginFormEnglish(self):
        result = asString(self.form.loginForm(session={}, path='/page/login2'))

        self.assertEqualsWS("""<div id="login-form">
    <form method="POST" name="login" action="/action">
    <input type="hidden" name="formUrl" value="/page/login2"/>
        <dl>
            <dt>Username</dt>
            <dd><input type="text" name="username" value=""/></dd>
            <dt>Password</dt>
            <dd><input type="password" name="password"/></dd>
            <dd class="submit"><input type="submit" value="Login"/></dd>
        </dl>
    </form>
</div>""", result)

    def testLoginFormDutch(self):
        result = asString(self.form.loginForm(session={}, path='/page/login2', lang='nl'))

        self.assertEqualsWS("""<div id="login-form">
    <form method="POST" name="login" action="/action">
    <input type="hidden" name="formUrl" value="/page/login2"/>
        <dl>
            <dt>Gebruikersnaam</dt>
            <dd><input type="text" name="username" value=""/></dd>
            <dt>Wachtwoord</dt>
            <dd><input type="password" name="password"/></dd>
            <dd class="submit"><input type="submit" value="Inloggen"/></dd>
        </dl>
    </form>
</div>""", result)

    def testNewUserFormEN(self):
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.newUserFormValues': {'errorMessage': 'BAD BOY'},
        }
        result = asString(self.form.newUserForm(session=session, path='/page/login2', returnUrl='/return'))
        self.assertEqualsWS("""<div id="login-new-user-form">
    <p class="error">BAD BOY</p>
    <form method="POST" name="newUser" action="/action/newUser">
    <input type="hidden" name="formUrl" value="/page/login2"/>
    <input type="hidden" name="returnUrl" value="/return"/>
        <dl>
            <dt>Username</dt>
            <dd><input type="text" name="username" value=""/></dd>
            <dt>Password</dt>
            <dd><input type="password" name="password"/></dd>
            <dt>Retype password</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="Create"/></dd>
        </dl>
    </form>
</div>""", result)

    def testNewUserFormNL(self):
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.newUserFormValues': {'errorMessage': 'BAD BOY'},
        }
        result = asString(self.form.newUserForm(session=session, path='/page/login2', returnUrl='/return', lang="nl"))
        self.assertEqualsWS("""<div id="login-new-user-form">
    <p class="error">BAD BOY</p>
    <form method="POST" name="newUser" action="/action/newUser">
    <input type="hidden" name="formUrl" value="/page/login2"/>
    <input type="hidden" name="returnUrl" value="/return"/>
        <dl>
            <dt>Gebruikersnaam</dt>
            <dd><input type="text" name="username" value=""/></dd>
            <dt>Wachtwoord</dt>
            <dd><input type="password" name="password"/></dd>
            <dt>Herhaal wachtwoord </dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="Aanmaken"/></dd>
        </dl>
    </form>
</div>""", result)

    def testRedirectOnGet(self):
        result = asString(self.form.handleRequest(path='/whatever', Client=('127.0.0.1', 3451), Method='GET'))
        header, body = result.split(CRLF*2)
        self.assertTrue('405' in header)

    def testLoginWithPOSTsucceedsRedirectsToOriginalPath(self):
        observer = CallTrace(onlySpecifiedMethods=True)
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = True
        Body = urlencode(dict(username='user', password='secret'))
        session = {ORIGINAL_PATH:'/please/go/here'}

        result = asString(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        self.assertEquals('user', session['user'].name)
        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /please/go/here' in header)
        user = session['user']
        self.assertFalse(user.isAdmin())

        self.assertEquals(['validateUser'], [m.name for m in observer.calledMethods])
        self.assertEquals({'username': 'user', 'password':'secret'}, observer.calledMethods[0].kwargs)

    def testLoginWithPOSTsucceedsRedirectsToOriginalPathOnlyOnce(self):
        observer = CallTrace(onlySpecifiedMethods=True)
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = True
        Body = urlencode(dict(username='user', password='secret'))
        session = {ORIGINAL_PATH:'/please/go/here'}

        result = asString(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        self.assertEquals('user', session['user'].name)
        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /please/go/here' in header)
        self.assertFalse(session['user'].isAdmin())

        self.assertEquals(['validateUser'], [m.name for m in observer.calledMethods])
        self.assertEquals({'username': 'user', 'password':'secret'}, observer.calledMethods[0].kwargs)

        result = asString(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /home' in header, header)

    def testLoginWithPOSTsucceeds(self):
        observer = CallTrace(onlySpecifiedMethods=True)
        def userIsAdmin(name):
            return True
        observer.methods['userIsAdmin'] = userIsAdmin
        self.form = BasicHtmlLoginForm(action='/action', loginPath='/login', home='/home', userIsAdminMethod=observer.userIsAdmin)
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = True
        Body = urlencode(dict(username='user', password='secret'))
        session = {}

        result = asString(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        self.assertEquals('user', session['user'].name)
        self.assertEquals(True, session['user'].isAdmin())
        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /home' in header)

        self.assertEquals(['validateUser', 'userIsAdmin'], [m.name for m in observer.calledMethods])
        self.assertEquals({'username': 'user', 'password':'secret'}, observer.calledMethods[0].kwargs)
        self.assertEquals(('user',), observer.calledMethods[-1].args)

    def testLoginWithPOSTfails(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = False
        Body = urlencode(dict(username='user', password='wrong'))
        session = {}

        result = asString(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        self.assertFalse('user' in session)
        self.assertEquals({'username':'user', 'errorMessage': 'Invalid username or password'}, session['BasicHtmlLoginForm.formValues'])
        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /login' in header, header)

        self.assertEquals(['validateUser'], [m.name for m in observer.calledMethods])
        self.assertEquals({'username': 'user', 'password':'wrong'}, observer.calledMethods[0].kwargs)

    def testLoginCreatesAUserByAnObserver(self):
        observer = CallTrace()
        user = dict(user='this object')
        observer.returnValues['validateUser'] = True
        observer.returnValues['userForName'] = user
        self.form.addObserver(observer)
        Body = urlencode(dict(username='user', password='secret'))
        session = {ORIGINAL_PATH:'/please/go/here'}

        consume(self.form.handleRequest(path='/login', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        self.assertEquals(user, session['user'])
        self.assertEquals(['validateUser', 'userForName'], observer.calledMethodNames())
        self.assertEquals(dict(username='user'), observer.calledMethods[-1].kwargs)


    def testLoginFormWithError(self):
        session = {}
        session['BasicHtmlLoginForm.formValues']={'username': '<us"er>', 'errorMessage': 'Invalid <username> or "password"'}
        result = asString(self.form.loginForm(session=session, path='/show/login'))

        self.assertEqualsWS("""<div id="login-form">
    <p class="error">Invalid &lt;username&gt; or "password"</p>
    <form method="POST" name="login" action="/action">
    <input type="hidden" name="formUrl" value="/show/login"/>
        <dl>
            <dt>Username</dt>
            <dd><input type="text" name="username" value='&lt;us"er&gt;'/></dd>
            <dt>Password</dt>
            <dd><input type="password" name="password"/></dd>
            <dd class="submit"><input type="submit" value="Login"/></dd>
        </dl>
    </form>
</div>""", result)

    def testShowChangePasswordFormEn(self):
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.formValues': {'errorMessage': 'BAD BOY'},
        }
        result = asString(self.form.changePasswordForm(session=session, path='/show/changepasswordform', arguments={}))

        self.assertEqualsWS("""<div id="login-change-password-form">
    <p class="error">BAD BOY</p>
    <form method="POST" name="changePassword" action="/action/changepassword">
    <input type="hidden" name="formUrl" value="/show/changepasswordform"/>
    <input type="hidden" name="username" value="username"/>
        <dl>
            <dt>Old password</dt>
            <dd><input type="password" name="oldPassword"/></dd>
            <dt>New password</dt>
            <dd><input type="password" name="newPassword"/></dd>
            <dt>Retype new password</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="Change"/></dd>
        </dl>
    </form>
</div>""", result)

    def testShowChangePasswordFormNl(self):
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.formValues': {'errorMessage': 'BAD BOY'},
        }
        result = asString(self.form.changePasswordForm(session=session, path='/show/changepasswordform', lang="nl", arguments={}))

        self.assertEqualsWS("""<div id="login-change-password-form">
    <p class="error">BAD BOY</p>
    <form method="POST" name="changePassword" action="/action/changepassword">
    <input type="hidden" name="formUrl" value="/show/changepasswordform"/>
    <input type="hidden" name="username" value="username"/>
        <dl>
            <dt>Oud wachtwoord</dt>
            <dd><input type="password" name="oldPassword"/></dd>
            <dt>Nieuw wachtwoord</dt>
            <dd><input type="password" name="newPassword"/></dd>
            <dt>Herhaal nieuw wachtwoord</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="Aanpassen"/></dd>
        </dl>
    </form>
</div>""", result)

    def testShowChangePasswordFormForSpecifiedUser(self):
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.formValues': {'errorMessage': 'BAD BOY'},
        }
        result = asString(self.form.changePasswordForm(session=session, path='/show/changepasswordform', lang="nl", arguments=dict(user=['myuser']), user='myuser', onlyNewPassword=True))

        self.assertEqualsWS("""<div id="login-change-password-form">
    <p class="error">BAD BOY</p>
    <form method="POST" name="changePassword" action="/action/changepassword">
    <input type="hidden" name="formUrl" value="/show/changepasswordform?user=myuser"/>
    <input type="hidden" name="username" value="myuser"/>
        <dl>
            <dt>Nieuw wachtwoord</dt>
            <dd><input type="password" name="newPassword"/></dd>
            <dt>Herhaal nieuw wachtwoord</dt>
            <dd><input type="password" name="retypedPassword"/></dd>
            <dd class="submit"><input type="submit" value="Aanpassen"/></dd>
        </dl>
    </form>
</div>""", result)

    def testShowChangePasswordFormErrorWithoutUser(self):
        session = {}
        result = asString(self.form.changePasswordForm(session=session, path='/show/changepasswordform', arguments={}))

        self.assertEqualsWS("""<div id="login-change-password-form">
    <p class="error">Please login to change password.</p>
</div>""", result)

    def testChangePasswordMismatch(self):
        Body = urlencode(dict(username='user', oldPassword='correct', newPassword="good", retypedPassword="mismatch", formUrl='/show/changepasswordform'))
        session = {'user': User('user')}

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals({'username':'user', 'errorMessage': 'New passwords do not match'}, session['BasicHtmlLoginForm.formValues'])
        self.assertEqualsWS("""HTTP/1.0 302 Found\r\nLocation: /show/changepasswordform\r\n\r\n""", result)

    def testChangePasswordWrongOld(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = False

        Body = urlencode(dict(username='user', oldPassword='wrong', newPassword="good", retypedPassword="good", formUrl='/show/changepasswordform'))
        session = {'user': User('user')}

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals({'username':'user', 'errorMessage': 'Username and password do not match.'}, session['BasicHtmlLoginForm.formValues'])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/changepasswordform\r\n\r\n", result)

    def testChangePasswordNoOldNotAllowed(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = False

        Body = urlencode(dict(username='username', newPassword="good", retypedPassword="good", formUrl='/show/changepasswordform'))
        session = {
            'user': User('username'),
            'BasicHtmlLoginForm.formValues': {}
        }

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals({'username':'username', 'errorMessage': 'Username and password do not match.'}, session['BasicHtmlLoginForm.formValues'])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/changepasswordform\r\n\r\n", result)

    def testChangePasswordNoOldForAdminOnlyAllowedForOtherUsers(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = False

        Body = urlencode(dict(username='user', newPassword="good", retypedPassword="good", formUrl='/show/changepasswordform'))
        session = {
            'user': User('admin'),
            'BasicHtmlLoginForm.formValues': {}
        }

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals(['changePassword'], [m.name for m in observer.calledMethods])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /home\r\n\r\n", result)

    def testChangePasswordNoOldForAdminNotAllowed(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = False

        Body = urlencode(dict(username='admin', newPassword="good", retypedPassword="good", formUrl='/show/changepasswordform'))
        session = {
            'user': User('admin'),
            'BasicHtmlLoginForm.formValues': {}
        }

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals({'username':'admin', 'errorMessage': 'Username and password do not match.'}, session['BasicHtmlLoginForm.formValues'])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/changepasswordform\r\n\r\n", result)

    def testChangePassword(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        observer.returnValues['validateUser'] = True

        Body = urlencode(dict( username='user', oldPassword='correct', newPassword="good", retypedPassword="good", formUrl='/show/changepasswordform'))
        session = {'user': User('user')}

        result = asString(self.form.handleRequest(path='/login/changepassword', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))
        self.assertEquals(['validateUser', 'changePassword'], [m.name for m in observer.calledMethods])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /home\r\n\r\n", result)


    def testDeleteUserNoAdmin(self):
        observer = CallTrace()
        self.form.addObserver(observer)
        result = asString(self.form.handleRequest(
            path='/login/remove',
            Client=('127.0.0.1', 3451),
            Method='POST',
            Body=urlencode(dict(username='user', formUrl='/show/userlist')),
            session={}))
        self.assertEquals([], [m.name for m in observer.calledMethods])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/userlist\r\n\r\n", result)

    def testDeleteUserAsAdmin(self):
        observer = CallTrace(returnValues={'hasUser': True})
        self.form.addObserver(observer)
        result = asString(self.form.handleRequest(
            path='/login/remove',
            Client=('127.0.0.1', 3451),
            Method='POST',
            Body=urlencode(dict(username='user', formUrl='/show/userlist')),
            session={'user': User('admin')}))

        self.assertEquals(['hasUser', 'removeUser'], [m.name for m in observer.calledMethods])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/userlist\r\n\r\n", result)

    def testDeleteNonExistingUser(self):
        observer = CallTrace(returnValues={'hasUser': False})
        self.form.addObserver(observer)
        session = {'user': User('admin')}
        result = asString(self.form.handleRequest(
            path='/login/remove',
            Client=('127.0.0.1', 3451),
            Method='POST',
            Body=urlencode(dict(username='user', formUrl='/show/userlist')),
            session=session))

        self.assertEquals(['hasUser'], [m.name for m in observer.calledMethods])
        self.assertEquals("HTTP/1.0 302 Found\r\nLocation: /show/userlist\r\n\r\n", result)
        self.assertEquals({'errorMessage': 'User "user" does not exist.'}, session['BasicHtmlLoginForm.formValues'])

    def testNewUserWithPOSTsucceeds(self):
        pf = PasswordFile(join(self.tempdir, 'passwd'))
        self.form.addObserver(pf)
        pf.addUser('existing', 'password')
        Body = urlencode(dict(username='newuser', password='secret', retypedPassword='secret', formUrl='/page/newUser', returnUrl='/return'))
        session = {'user':User('existing')}

        result = asString(self.form.handleRequest(path='/action/newUser', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /return' in header)

        self.assertEquals(set(['existing', 'newuser', 'admin']), set(pf.listUsernames()))
        self.assertTrue(pf.validateUser('newuser', 'secret'))
        self.assertEquals('Added user "newuser"', session['BasicHtmlLoginForm.newUserFormValues']['successMessage'])

    def testNewUserWithPOSTFails(self):
        pf = PasswordFile(join(self.tempdir, 'passwd'))
        self.form.addObserver(pf)
        pf.addUser('existing', 'password')
        pf.addUser('newuser', 'oldpassword')
        Body = urlencode(dict(username='newuser', password='newpassword', retypedPassword='newpassword', formUrl='/page/newUser', returnUrl='/return'))
        session = {'user':User('existing')}

        result = asString(self.form.handleRequest(path='/action/newUser', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /page/newUser' in header)

        self.assertEquals(set(['existing', 'newuser', 'admin']), set(pf.listUsernames()))
        self.assertTrue(pf.validateUser('newuser', 'oldpassword'))
        self.assertFalse(pf.validateUser('newuser', 'newpassword'))
        self.assertEquals({'errorMessage':'User already exists.', 'username':'newuser'}, session['BasicHtmlLoginForm.newUserFormValues'])

    def testNewUserWithPOSTFailsDifferentPasswords(self):
        pf = PasswordFile(join(self.tempdir, 'passwd'))
        self.form.addObserver(pf)
        pf.addUser('existing', 'password')
        Body = urlencode(dict(username='newuser', password='newpassword', retypedPassword='retypedpassword', formUrl='/page/newUser', returnUrl='/return'))
        session = {'user':User('existing')}

        result = asString(self.form.handleRequest(path='/action/newUser', Client=('127.0.0.1', 3451), Method='POST', Body=Body, session=session))

        header, body = result.split(CRLF*2)
        self.assertTrue('302' in header)
        self.assertTrue('Location: /page/newUser' in header)

        self.assertEquals(set(['existing', 'admin']), set(pf.listUsernames()))
        self.assertEquals({'errorMessage':'Passwords do not match', 'username':'newuser'}, session['BasicHtmlLoginForm.newUserFormValues'])

    def testShowUserList(self):
        pf = PasswordFile(join(self.tempdir, 'passwd'))
        self.form.addObserver(pf)
        pf.addUser('one', 'password')
        pf.addUser('two', 'password')
        pf.addUser('three', 'password')

        session = {'user':User('two', isAdminMethod=lambda name:True)}

        result = asString(self.form.userList(session=session, path='/show/login'))

        self.assertEqualsWS("""<div id="login-user-list">
    <script type="text/javascript">
function deleteUser(username) {
    if (confirm("Are you sure?")) {
        document.removeUser.username.value = username;
        document.removeUser.submit();
    }
}
</script>
<form name="removeUser" method="POST" action="/action/remove">
    <input type="hidden" name="formUrl" value="/show/login"/>
    <input type="hidden" name="username"/>
</form>
    <ul>
        <li>admin <a href="javascript:deleteUser('admin');">delete</a></li>
        <li>one <a href="javascript:deleteUser('one');">delete</a></li>
        <li>three <a href="javascript:deleteUser('three');">delete</a></li>
        <li>two</li>
    </ul>
</div>""", result)

    def testShowUserListWithUserLink(self):
        pf = PasswordFile(join(self.tempdir, 'passwd'))
        self.form.addObserver(pf)
        pf.addUser('one', 'password')
        pf.addUser('two', 'password')
        pf.addUser('three', 'password')

        session = {'user':User('two', isAdminMethod=lambda name:True)}

        result = asString(self.form.userList(session=session, path='/show/login', userLink='/user'))

        self.assertEqualsWS("""<div id="login-user-list">
    <script type="text/javascript">
function deleteUser(username) {
    if (confirm("Are you sure?")) {
        document.removeUser.username.value = username;
        document.removeUser.submit();
    }
}
</script>
<form name="removeUser" method="POST" action="/action/remove">
    <input type="hidden" name="formUrl" value="/show/login"/>
    <input type="hidden" name="username"/>
</form>
    <ul>
        <li><a href="/user?user=admin">admin</a> <a href="javascript:deleteUser('admin');">delete</a></li>
        <li><a href="/user?user=one">one</a> <a href="javascript:deleteUser('one');">delete</a></li>
        <li><a href="/user?user=three">three</a> <a href="javascript:deleteUser('three');">delete</a></li>
        <li><a href="/user?user=two">two</a></li>
    </ul>
</div>""", result)

    def testBroadcastAddUserToAllObservers(self):
        values = []
        dna = be(
            (Observable(),
                (BasicHtmlLoginForm(action="/action", loginPath="/"),
                    (CallTrace(methods={'addUser': lambda *args, **kwargs: values.append(("1st", args, kwargs))}),),
                    (CallTrace(methods={'addUser': lambda *args, **kwargs: values.append(("2nd", args, kwargs))}),),
                    (CallTrace(methods={'addUser': lambda *args, **kwargs: values.append(("3rd", args, kwargs))}),),
                )
            )
        )

        asString(dna.all.handleNewUser(session={}, Body=urlencode(dict(password="password", retypedPassword="password"))))
        self.assertEquals(3, len(values))
