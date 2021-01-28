## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2012 Meertens Instituut (KNAW) http://meertens.knaw.nl
# Copyright (C) 2012-2018, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
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

from seecr.test import SeecrTestCase
from seecr.test.io import stdout_replaced
from simplejson import dump as jsonSave, dump, load

from os.path import join
from meresco.html.login import PasswordFile
from meresco.html.login.passwordfile import md5Hash
from meresco.components.json import JsonDict
import warnings

poorHash = lambda data: ''.join(reversed(data))

class PasswordFileTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.filename=join(self.tempdir, 'passwd')
        with stdout_replaced() as self.stdout:
            self.pwd = PasswordFile(filename=self.filename, hashMethod=poorHash)

    def testReadPasswordFile(self):
        passwdHash = poorHash('passwordsalt')
        data = JsonDict(users={'John':{'salt':'salt', 'password':passwdHash}}, version=PasswordFile.version)
        data.dump(self.filename)
        pf = PasswordFile(filename=self.filename, hashMethod=poorHash)
        self.assertTrue(pf.validateUser('John', 'password'))

    def testAddUser(self):
        self.pwd.addUser(username='John', password='password')
        self.assertTrue(self.pwd.validateUser('John', 'password'))
        # reopen file.
        pf = PasswordFile(filename=self.filename, hashMethod=poorHash)
        self.assertTrue(pf.validateUser('John', 'password'))

    def testValidPassword(self):
        self.pwd.addUser(username='John', password='password')
        self.assertFalse(self.pwd.validateUser(username='John', password=''))
        self.assertFalse(self.pwd.validateUser(username='John', password=' '))
        self.assertFalse(self.pwd.validateUser(username='John', password='abc'))
        self.assertTrue(self.pwd.validateUser(username='John', password='password'))
        self.assertFalse(self.pwd.validateUser(username='John', password='password '))

        self.assertFalse(self.pwd.validateUser(username='', password=''))
        self.assertFalse(self.pwd.validateUser(username='Piet', password=''))

    def testSetPassword(self):
        self.pwd.addUser(username='John', password='password')
        self.pwd.setPassword(username='John', password='newpasswd')
        self.assertTrue(self.pwd.validateUser(username='John', password='newpasswd'))

    def testSetPasswordWithBadUsername(self):
        self.assertRaises(ValueError, self.pwd.setPassword, username='Harry', password='newpasswd')

    def testPasswordTest(self):
        self.assertTrue(self.pwd._passwordTest('something'))
        self.assertTrue(self.pwd._passwordTest('s om et hing'))
        self.assertTrue(self.pwd._passwordTest('ng'))
        self.assertTrue(self.pwd._passwordTest('SOMETHING'))
        self.assertTrue(self.pwd._passwordTest('123513'))
        self.assertFalse(self.pwd._passwordTest(''))
        self.assertFalse(self.pwd._passwordTest(' '))
        self.assertFalse(self.pwd._passwordTest('\t'))
        self.assertFalse(self.pwd._passwordTest('\t\n'))

    def testAddUserWithBadPassword(self):
        self.assertRaises(ValueError, self.pwd.addUser, username='Harry', password='')

    def testAddUserWithBadname(self):
        self.assertRaises(ValueError, self.pwd.addUser, username='', password='good')

    def testChangePasswordWithBadPassword(self):
        self.pwd.addUser(username='Harry', password='good')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            self.assertRaises(ValueError, self.pwd.changePassword, username='Harry', oldPassword='good', newPassword='')

    def testChangePasswordWithEmptyOldPassword(self):
        self.pwd.addUser(username='Harry', password='good')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            self.pwd.changePassword(username='Harry', oldPassword=None, newPassword='good2')
        self.assertFalse(self.pwd.validateUser(username='Harry', password='good'))
        self.assertTrue(self.pwd.validateUser(username='Harry', password='good2'))

    def testUsernameTest(self):
        self.assertTrue(self.pwd._usernameTest('name'))
        self.assertTrue(self.pwd._usernameTest('name@domain.com'))
        self.assertTrue(self.pwd._usernameTest('name-1235'))
        self.assertFalse(self.pwd._usernameTest('name\t-1235'))
        self.assertFalse(self.pwd._usernameTest(''))
        self.assertFalse(self.pwd._usernameTest(' '))
        self.assertFalse(self.pwd._usernameTest(' name'))

    def testAddExistingUser(self):
        self.pwd.addUser(username='John', password='password')
        self.assertRaises(ValueError, self.pwd.addUser, username='John', password='good')

    def testAddMultipleUsers(self):
        self.pwd.addUser(username='John', password='password')
        self.pwd.addUser(username='Johnny', password='password2')
        self.pwd.addUser(username='Johann', password='password3')
        self.assertTrue(self.pwd.validateUser('John', 'password'))
        self.assertTrue(self.pwd.validateUser('Johnny', 'password2'))
        self.assertTrue(self.pwd.validateUser('Johann', 'password3'))

    def testRemoveUser(self):
        self.pwd.addUser(username='John', password='password')
        self.assertTrue(self.pwd.validateUser('John', 'password'))
        self.pwd.removeUser(username='John')
        self.assertFalse(self.pwd.validateUser('John', 'password'))

    def testListUsernames(self):
        self.pwd.addUser(username='john', password='password')
        self.pwd.addUser(username='graham', password='password2')
        self.pwd.addUser(username='hank', password='password3')
        self.assertEqual(set(['admin', 'hank', 'graham', 'john']), set(self.pwd.listUsernames()))

    def testHasUser(self):
        self.pwd.addUser(username='john', password='password')
        self.assertTrue(self.pwd.hasUser(username='john'))
        self.assertFalse(self.pwd.hasUser(username='johnny'))

    def testCreateFileIfMissingWithDefaultAdmin(self):
        pw = self.stdout.getvalue().split('"')[3]
        self.assertTrue(self.pwd.validateUser(username='admin', password=pw))

    def testConvert(self):
        userstxt = join(self.tempdir, 'users.txt')
        with open(userstxt, 'w') as f:
            f.write('user1:{0}\nuser2:{1}'.format(md5Hash('secret1'), md5Hash('secret2')))
        pwd = PasswordFile.convert(userstxt, self.filename)
        self.assertTrue(pwd.validateUser('user1', 'secret1'))

    def testCreateSaltAfterConversion(self):
        tmpfile = join(self.tempdir, 'passwdwithoutsalt')
        JsonDict(users=dict(username=dict(salt='', password=md5Hash('secret'))), version=PasswordFile.version).dump(tmpfile)
        pwd = PasswordFile(tmpfile)
        self.assertTrue(pwd.validateUser('username', 'secret'))
        d = JsonDict.load(tmpfile)
        self.assertTrue(5, len(d['users']['username']['salt']))
        pwd = PasswordFile(tmpfile)
        self.assertTrue(pwd.validateUser('username', 'secret'))

    def testEmptyPasswordfile(self):
        pwd = PasswordFile(join(self.tempdir, 'empty'), createAdminUserIfEmpty=False)
        self.assertEqual([], pwd.listUsernames())

    @stdout_replaced
    def testParameterizedStorage(self):
        args = []
        class Storage(object):
            def store(self, id_, data):
                args.append((id_, data))
            def retrieve(self, id_):
                if len(args) < 1 or args[-1][0] != id_:
                    raise KeyError
                data = args[-1][1]
                return data
        pwd = PasswordFile('a name', storage=Storage())
        pwd.addUser(username='erik', password='insect')
        id_, data = args[-1]
        self.assertEqual('a name', id_)
        self.assertTrue('erik' in data) # I believe. More elaborate tests above.
