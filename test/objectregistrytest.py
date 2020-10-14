## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2013-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from seecr.test import SeecrTestCase, CallTrace

from meresco.html import ObjectRegistry
from urllib.parse import urlencode
from weightless.core import asString
from weightless.http import parseHeadersString
from meresco.components.http.utils import CRLF
from meresco.html.objectregistry import ObjectRegistryException
from uuid import uuid4

class ObjectRegistryTest(SeecrTestCase):
    def testAddDelete(self):
        observer = CallTrace('observer')
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.addObserver(observer)
        registry.registerKeys(keys=['name', 'key2', 'another'], booleanKeys=['enabled', 'feature'])
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'])
        object2id = registry.addObject(name=["object2"], key2=["value_2"], enabled=['on'])
        self.assertEqual({
                object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1', 'another':'', 'feature': False},
                object2id: {'key2': 'value_2', 'enabled': True, 'name': 'object2', 'another':'', 'feature': False}
            }, registry.listObjects())
        self.assertEqual(['objectAdded', 'objectAdded'], observer.calledMethodNames())
        self.assertEqual({'name':'name', 'identifier': object1id}, observer.calledMethods[0].kwargs)
        observer.calledMethods.reset()
        registry.removeObject(identifier=object2id)
        self.assertEqual(['objectRemoved'], observer.calledMethodNames())
        self.assertEqual({'name':'name', 'identifier': object2id}, observer.calledMethods[0].kwargs)
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEqual({
                object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1', 'another':'', 'feature': False},
            }, registry.listObjects())

    def testPersistent(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key2', 'name'], booleanKeys=['enabled'])
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'])

        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEqual(
                {object1id: {'key2': 'value_1', 'enabled': True, 'name': 'object1'}},
                registry.listObjects())

    def testUpdateObject(self):
        observer = CallTrace('observer')
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.addObserver(observer)
        registry.registerKeys(keys=['key2', 'name'], booleanKeys=['enabled'])
        object1id = registry.addObject(name=["object1"], key2=["value_1"], enabled=['on'])
        registry.updateObject(identifier=object1id, name=["object1"], key2=["value_2"])
        self.assertEqual(['objectAdded', 'objectUpdated'], observer.calledMethodNames())
        self.assertEqual({'name':'name', 'identifier': object1id}, observer.calledMethods[-1].kwargs)
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEqual({
                object1id: {'key2': 'value_2', 'enabled': False, 'name': 'object1'}
            }, registry.listObjects())

    def testPartialUpdateObject(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key0', 'key1'], booleanKeys=['enabled0', 'enabled1'])
        object1id = registry.addObject(key0=["value0"], key1=["value1"], enabled0=['on'], enabled1=['on'])
        self.assertEqual({
                object1id: {'key0': 'value0', 'enabled0': True, 'key1': 'value1', 'enabled1': True}
            }, registry.listObjects())
        registry.updateObject(identifier=object1id, __booleanKeys__=['enabled1'])
        self.assertEqual({
                object1id: {'key0': 'value0', 'enabled0': True, 'key1': 'value1', 'enabled1': False}
            }, registry.listObjects())
        registry.updateObject(identifier=object1id, __booleanKeys__=['enabled1'], enabled1=['on'])
        self.assertEqual({
                object1id: {'key0': 'value0', 'enabled0': True, 'key1': 'value1', 'enabled1': True}
            }, registry.listObjects())

        registry.updateObject(identifier=object1id, __booleanKeys__=[''])
        self.assertEqual({
                object1id: {'key0': 'value0', 'enabled0': True, 'key1': 'value1', 'enabled1': True}
            }, registry.listObjects())

    def testUpdateObjectWithNonexistingIdentfier(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key0', 'key1'])
        identifier = str(uuid4())
        self.assertRaises(ObjectRegistryException, lambda: registry.updateObject(identifier=identifier, key0=['value']))

        data = urlencode([
                ('identifier', identifier),
                ('key1', 'value1'),
            ])
        session = {}
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/update', Body=data, session=session)).split(CRLF*2)
        self.assertEqual({"ObjectRegistry" : {
                'error': "Identifier '{0}' does not exist.".format(identifier),
                'values': {
                    'identifier': [identifier],
                    'key1': ['value1']
                }
            }}, session)

    def testAddWithExistingId(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key0', 'key1'])
        object1id = registry.addObject(key0=["value0"], key1=["value1"])
        self.assertRaises(ObjectRegistryException, lambda: registry.addObject(identifier=object1id, key0=["value0"], key1=["value1"]))


    def testAddObjectWithGivenIdentifier(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key0', 'key1'])
        identifier = str(uuid4())
        object1id = registry.addObject(identifier=identifier, key0=["value0"], key1=["value1"])
        self.assertEqual(identifier, object1id)

    def testAddObjectIdentifierMustBeUUID(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key0', 'key1'])
        self.assertRaises(ObjectRegistryException, lambda: registry.addObject(identifier='identifier', key0=["value0"], key1=["value1"]))

    def testUpdateChangeKeys(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['one', 'two'], booleanKeys=['three'])
        object1id = registry.addObject(one=["one"], two=["two"], three=['on'])
        registry.registerKeys(keys=['one', 'four'], booleanKeys=['three'])
        registry.updateObject(identifier=object1id, one=["one"], four=["four"])
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        self.assertEqual({
                object1id: {'one': 'one', 'three': False, 'four': 'four'}
            }, registry.listObjects())

    def testPostRequest(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key1', 'key2'], booleanKeys=['enabled1', 'enabled2'])
        data = urlencode([
                ('key1', 'value1'),
                ('enabled1', 'on'),
            ])
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/add', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeadersString(header+CRLF)['Location']
        path, objectid = redirectLocation.split('#')
        self.assertEqual('/redirect', path)
        self.assertEqual({
                objectid: {'key1': 'value1', 'key2': '', 'enabled1': True, 'enabled2': False}
            }, registry.listObjects())

    def testRedirectWithPostedRedirectPath(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key1', 'key2'], booleanKeys=['enabled1', 'enabled2'])
        data = urlencode([
                ('key1', 'value1'),
                ('enabled1', 'on'),
                ('redirectPath', '/object?id={}')
            ])
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/add', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeadersString(header+CRLF)['Location']
        path, objectid = redirectLocation.split('=')
        self.assertEqual('/object?id', path)
        self.assertEqual({
                objectid: {'key1': 'value1', 'key2': '', 'enabled1': True, 'enabled2': False}
            }, registry.listObjects())

    def testRedirectWithPostedRedirectPathButWithoutIdentifier(self):
        def validate(**kwargs):
            raise ValueError('oops')
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect', validate=validate)
        registry.registerKeys(keys=['key1', 'key2'], booleanKeys=['enabled1', 'enabled2'])
        data = urlencode([
                ('key1', 'value1'),
                ('enabled1', 'on'),
                ('redirectPath', '/object?id={}')
            ])
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/add', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeadersString(header+CRLF)['Location']
        path, objectid = redirectLocation.split('#')
        self.assertEqual('/redirect', path)
        self.assertEqual('', objectid)
        self.assertEqual({}, registry.listObjects())

    def testNoKeySendDoesNotChangeOldValue(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key2', 'key1'], booleanKeys=['enabled1', 'enabled2'])
        object1id = registry.addObject(key1=["object1"], key2=["value2"], enabled1=['on'])
        self.assertEqual({
                'key1': 'object1',
                'key2': 'value2',
                'enabled1': True,
                'enabled2': False,
            }, registry.listObjects()[object1id])
        data = urlencode([
                ('identifier', object1id),
                ('key1', 'value1'),
                ('enabled2', 'on'),
            ])
        header, _ = asString(registry.handleRequest(Method='POST', path='/objects/update', Body=data, session={})).split(CRLF*2)
        redirectLocation = parseHeadersString(header+CRLF)['Location']
        path, objectid = redirectLocation.split('#')
        self.assertEqual(object1id, objectid)
        self.assertEqual({
                'key1': 'value1',
                'key2': 'value2',
                'enabled1': False,
                'enabled2': True,
            }, registry.listObjects()[object1id])

    def testRegister(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(keys=['key1', 'key2'], booleanKeys=['enabled1', 'enabled2'])
        object1id = registry.addObject(key1=["object1"], enabled1=['on'])
        self.assertEqual({
                'key1': 'object1',
                'key2': '',
                'enabled1': True,
                'enabled2': False,
            }, registry.listObjects()[object1id])

    def testJsondict(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(jsonKeys=['key1', 'key2'])
        object1id = registry.addObject(key1=['{"key":"needsvalue"}'])
        self.assertEqual({
                'key1': {'key':'needsvalue'},
                'key2': {},
            }, registry.listObjects()[object1id])

    def testValidate(self):
        def validate(*args, **kwargs):
            raise ValueError()
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect', validate=validate)
        registry.registerKeys(keys=['key'])
        self.assertRaises(ValueError, lambda: registry.addObject(key=['value']))

    def testDefaults(self):
        defaults = [
            {"name": "object1", "key2": "value_1", "enabled": True},
            {"name": "object2", "key2": "value_2", "enabled": True},
        ]
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect', defaults=defaults)
        registry.registerKeys(keys=['name', 'key2'], booleanKeys=['enabled'])
        objs = registry.listObjects()
        self.assertEqual(2, len(objs))
        self.assertEqual([
                {'key2': 'value_1', 'enabled': True, 'name': 'object1'},
                {'key2': 'value_2', 'enabled': True, 'name': 'object2'}
            ], list(objs.values()))

    def testListKeys(self):
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect')
        registry.registerKeys(listKeys=['choices', 'others'])
        id = registry.addObject(choices=['one', 'two'])
        objs = registry.listObjects()
        self.assertEqual(1, len(objs))
        self.assertEqual(
                {'choices': ['one', 'two'], 'others':[]},
                objs[id])

    def testGetConfiguration(self):
        defaults = [
            {"name": "object1", "key2": "value_1", "enabled": True},
            {"name": "object2", "key2": "value_2", "enabled": True},
        ]
        registry = ObjectRegistry(self.tempdir, name='name', redirectPath='/redirect', defaults=defaults)
        registry.registerKeys(keys=['name', 'key2'], booleanKeys=['enabled'])
        objs = registry.getConfiguration(key='whatever')
        self.assertEqual([
                {'key2': 'value_1', 'enabled': True, 'name': 'object1'},
                {'key2': 'value_2', 'enabled': True, 'name': 'object2'}
            ], list(objs.values()))


