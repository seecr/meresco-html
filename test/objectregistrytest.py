## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to registryide a new search service
#  for all public libraries in the Netherlands.
#
# Copyright (C) 2013-2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import SeecrTestCase

from seecr.html import ObjectRegistry
from urllib import urlencode
from weightless.core import asString
from weightless.http import parseHeaders
from meresco.components.http.utils import CRLF

class ObjectRegistryTest(SeecrTestCase):
    def testAddDelete(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        keysDict = dict(__keys__=['name', 'key2', 'another'], __booleanKeys__=['enabled', 'feature'])
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'], **keysDict)
        object2id = registry.addObject(name=["object2"], key2=["value_2"], enabled=['on'], **keysDict)
        self.assertEquals({
                object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1', 'another':'', 'feature': False},
                object2id: {'key2': 'value_2', 'enabled': True, 'name': 'object2', 'another':'', 'feature': False}
            }, registry.listObjects())
        registry.removeObject(identifier=object2id)
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEquals({
                object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1', 'another':'', 'feature': False},
            }, registry.listObjects())

    def testPersistent(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'], __keys__=['key2', 'name'], __booleanKeys__=['enabled'])

        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEquals(
                {object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1'}},
                registry.listObjects())

    def testUpdateObject(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'], __keys__=['key2', 'name'], __booleanKeys__=['enabled'])
        registry.updateObject(identifier=object1id, name=["object1"], key2=["value_2"], __keys__=['key2', 'name'], __booleanKeys__=['enabled'])
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEquals({
                object1id: {'key2': 'value_2', 'enabled': False, 'name': 'object1'}
            }, registry.listObjects())

    def testUpdateChangeKeys(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        object1id = registry.addObject(one=["one"], two=["two"], three=['on'], __keys__=['one', 'two'], __booleanKeys__=['three'])
        registry.updateObject(identifier=object1id, one=["one"], four=["four"], __keys__=['one', 'four'], __booleanKeys__=['three'])
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEquals({
                object1id: {'one': 'one', 'three': False, 'four': 'four'}
            }, registry.listObjects())

    def testPostRequest(self):
        data = urlencode([
                ('key1', 'value1'),
                ('enabled1', 'on'),
                ('__keys__', ','.join(['key1', 'key2'])),
                ('__booleanKeys__', ','.join(['enabled1', 'enabled2'])),
            ])
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/add', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeaders(header+CRLF)['Location']
        path, objectid = redirectLocation.split('#')
        self.assertEquals('/redirect', path)
        self.assertEquals({
                objectid: {'key1': 'value1', 'key2': '', 'enabled1': True, 'enabled2': False}
            }, registry.listObjects())

    def testNoKeySendDoesNotChangeOldValue(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        object1id = registry.addObject(key1=["object1"], key2=["value2"], enabled1=['on'], __keys__=['key2', 'key1'], __booleanKeys__=['enabled1', 'enabled2'])
        self.assertEquals({
                'key1': 'object1',
                'key2': 'value2',
                'enabled1': True,
                'enabled2': False,
            }, registry.listObjects()[object1id])
        data = urlencode([
                ('identifier', object1id),
                ('key1', 'value1'),
                ('enabled2', 'on'),
                ('__keys__', ','.join(['key1', 'key2'])),
                ('__booleanKeys__', ','.join(['enabled1', 'enabled2'])),
            ])
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/update', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeaders(header+CRLF)['Location']
        path, objectid = redirectLocation.split('#')
        self.assertEquals(object1id, objectid)
        self.assertEquals({
                'key1': 'value1',
                'key2': 'value2',
                'enabled1': False,
                'enabled2': True,
            }, registry.listObjects()[object1id])


