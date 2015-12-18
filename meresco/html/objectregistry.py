## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os.path import join, isfile, isdir
from os import makedirs
from simplejson import load, dump
from cgi import parse_qs

from meresco.components.http.utils import redirectHttp

from meresco.html import PostActions
from uuid import uuid4, UUID
from meresco.components.json import JsonDict
from .labels import getLabel

class ObjectRegistry(PostActions):
    def __init__(self, stateDir, name, redirectPath, lang='en', validate=None, **kwargs):
        PostActions.__init__(self, name=name, **kwargs)
        self._name = name
        isdir(stateDir) or makedirs(stateDir)
        self._registryFile = join(stateDir, "registry_{0}.json".format(self._name))
        self._redirectPath = redirectPath
        self._lang = lang
        self._validate = validate if validate else lambda *args, **kwargs: None
        if not isfile(self._registryFile):
            self._save({})

        self._register = {}
        self.registerKeys()

        self.registerAction('add', self.handleAdd)
        self.registerAction('update', self.handleUpdate)
        self.registerAction('remove', self.handleRemove)

    def addObject(self, identifier=None, **kwargs):
        values = self.listObjects()
        if identifier:
            try:
                identifier = str(UUID(identifier))
            except ValueError:
                raise ObjectRegistryException('badIdentifier', identifier=identifier)
        else:
            identifier = str(uuid4())
        self._add(values, identifier=identifier, **kwargs)
        self.do.objectAdded(name=self._name, identifier=identifier)
        return identifier

    def removeObject(self, identifier):
        values = self.listObjects()
        if identifier in values:
            del values[identifier]
        self._save(values)
        self.do.objectRemoved(name=self._name, identifier=identifier)

    def updateObject(self, identifier, **kwargs):
        values = self.listObjects()
        if identifier not in values:
            raise ObjectRegistryException('unexistingIdentifier', identifier=identifier)
        self._add(values, identifier=identifier, **kwargs)
        self.do.objectUpdated(name=self._name, identifier=identifier)
        return identifier

    def _add(self, values, identifier, **kwargs):
        self._validate(self, identifier=identifier, **kwargs)
        olddata = values.get(identifier, {})
        data = dict()
        for key in self._register['keys']:
            data[key] = kwargs.get(key, [olddata.get(key, '')])[0]
        for key in self._register['jsonKeys']:
            newdata = kwargs.get(key, [None])[0]
            if newdata is None and key in olddata:
                data[key] = olddata[key]
                continue
            data[key] = JsonDict.loads(newdata or '{}')
        for key in self._register['booleanKeys']:
            data[key] = olddata.get(key, False)
        for key in kwargs.get('__booleanKeys__', self._register['booleanKeys']):
            if not key:
                continue
            data[key] = key in kwargs
        values[identifier] = data
        self._save(values)

    def getConfiguration(self):
        return self.listObjects()

    def listObjects(self):
        return load(open(self._registryFile))

    def registerKeys(self, keys=None, booleanKeys=None, jsonKeys=None):
        self._register['keys'] = keys or []
        self._register['booleanKeys'] = booleanKeys or []
        self._register['jsonKeys'] = jsonKeys or []

    def registerConversion(self, **kwargs):
        self._register['json'] = kwargs.keys()

    def _handle(self, method, Body, session, **kwargs):
        formValues = parse_qs(Body, keep_blank_values=True)
        identifier = formValues.pop('identifier', [None])[0]
        try:
            identifier = method(
                    identifier=identifier,
                    **formValues
                )
        except ObjectRegistryException, e:
            session['ObjectRegistry'] = dict(
                error=getLabel(self._lang, 'objectRegistry', e.code).format(**e.kwargs),
                values=dict(identifier=[identifier], **formValues)
            )
        except Exception, e:
            session['ObjectRegistry'] = dict(
                error=getLabel(self._lang, 'objectRegistry', "unexpectedException").format(str(e)),
                values=dict(identifier=[identifier], **formValues)
            )
        yield redirectHttp % "{0}#{1}".format(self._redirectPath, identifier or '')

    def handleAdd(self, **kwargs):
        yield self._handle(method=self.addObject, **kwargs)

    def handleUpdate(self, **kwargs):
        yield self._handle(method=self.updateObject, **kwargs)

    def handleRemove(self, Body, **kwargs):
        formValues = parse_qs(Body)
        self.removeObject(identifier=formValues['identifier'][0])
        yield redirectHttp % self._redirectPath

    def _save(self, values):
        dump(values, open(self._registryFile, "w"))

class ObjectRegistryException(Exception):
    def __init__(self, code, **kwargs):
        Exception.__init__(self, code)
        self.code = code
        self.kwargs = kwargs