## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2013-2014, 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from meresco.core import Observable
from meresco.components.http.utils import findCookies, insertHeader
from weightless.core import compose

class RememberMeCookie(Observable):

    def handleRequest(self, session, Headers, **kwargs):
        extraHeader = None
        if 'user' not in session:
            cookieName = self.call.cookieName()
            for cookie in findCookies(Headers=Headers, name=cookieName):
                cookieDict = self.call.validateCookie(cookie)
                if cookieDict is not None:
                    session['user'] = cookieDict['value']
                    extraHeader = cookieDict['header']
                    break

        yield insertHeader(
            compose(self.all.handleRequest(session=session, Headers=Headers, **kwargs)),
            extraHeader
        )
