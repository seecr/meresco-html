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
from meresco.components.http.utils import methodNotAllowedHtml, successNoContentPlainText

class PostActions(Observable):
    def __init__(self,  name=None):
        Observable.__init__(self, name=name)
        self._default = None
        self._actions = {}

    def registerAction(self, name, method):
        self._actions[name] = method

    def defaultAction(self, method):
        self._default = method

    def handleRequest(self, Method, path, **kwargs):
        if Method.upper() != 'POST':
            yield methodNotAllowedHtml(allowed=['POST'])
            yield "<h1>Method Not Allowed</h1>"
            return

        ignored, action = path.rsplit('/', 1)
        if action in self._actions:
            yield self._actions[action](path=path, **kwargs)
            return
        if self._default is None:
            yield successNoContentPlainText
            yield "No Content"
            return

        yield self._default(path=path, **kwargs)
