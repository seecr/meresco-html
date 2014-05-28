## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
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

from os.path import join, isfile, isdir
from os import makedirs
from simplejson import load, dump
from cgi import parse_qs

from meresco.components.http.utils import redirectHttp

from seecr.html import PostActions
from uuid import uuid4

class ObjectRegistry(PostActions):
    def __init__(self, stateDir, name, redirectPath, **kwargs):
        super(ObjectRegistry, self).__init__(name=name, **kwargs)
        isdir(stateDir) or makedirs(stateDir)
        self._registryFile = join(stateDir, "registry_{0}.json".format(name))
        self._redirectPath = redirectPath
        if not isfile(self._registryFile):
            self._save({})

        self.registerAction('add', self.handleAdd)
        self.registerAction('update', self.handleUpdate)
        self.registerAction('remove', self.handleRemove)

    def addObject(self, identifier='ignored', **kwargs):
        values = self.listObjects()
        identifier = str(uuid4())
        self._add(values, identifier=identifier, **kwargs)
        return identifier

    def removeObject(self, identifier):
        values = self.listObjects()
        if identifier in values:
            del values[identifier]
        self._save(values)

    def updateObject(self, identifier, **kwargs):
        values = self.listObjects()
        self._add(values, identifier=identifier, **kwargs)
        return identifier

    def _add(self, values, identifier, __keys__, __booleanKeys__, **kwargs):
        olddata = values.get(identifier, {})
        data = dict()
        for key in __keys__:
            data[key] = kwargs.get(key, [olddata.get(key, '')])[0]
        for key in __booleanKeys__:
            data[key] = key in kwargs
        values[identifier] = data
        self._save(values)

    def listObjects(self):
        return load(open(self._registryFile))

    def _handle(self, method, Body, session, **kwargs):
        formValues = parse_qs(Body, keep_blank_values=True)
        identifier = formValues.pop('identifier', [None])[0]
        keys = formValues.pop('__keys__')[0].split(',')
        booleanKeys = formValues.pop('__booleanKeys__')[0].split(',')
        try:
            identifier = method(
                    identifier=identifier,
                    __keys__=keys,
                    __booleanKeys__=booleanKeys,
                    **formValues
                )
        except ValueError, e:
            session['error'] = str(e)
        yield redirectHttp % "{0}#{1}".format(self._redirectPath, identifier)

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

