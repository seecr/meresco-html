## begin license ##
#
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml".
#
# Copyright (C) 2013-2014 Seecr (Seek You Too B.V.) http://seecr.nl
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

from meresco.core import Observable

class RememberMeCookie(Observable):

    def handleRequest(self, session, **kwargs):
        Headers = kwargs.get('Headers', {})

        if Headers and 'Cookie' in Headers and 'user' not in session:
            cookieName = self.call.cookieName()
            for cookie in Headers.get('Cookie','').split(';'):
                name, value = cookie.strip().split("=", 1)
                if name == cookieName:
                    user = self.call.validateCookie(value)
                    if user:
                        session['user'] = user
                        break

        yield self.all.handleRequest(session=session, **kwargs)

