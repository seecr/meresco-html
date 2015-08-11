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
from meresco.components.http.utils import redirectHttp
from labels import getLabel

class SecureZone(Observable):
    def __init__(self, loginPath, excluding=None, defaultLanguage='en', rememberMeCookieName=None, rememberMeCookieMethod=None):
        Observable.__init__(self)
        self._loginPath = loginPath
        self._defaultLanguage = defaultLanguage
        self._excluding = [] if excluding is None else excluding
        self._rememberMeCookieName = rememberMeCookieName
        self._rememberMeCookieMethod = rememberMeCookieMethod

    def handleRequest(self, session, path, query, arguments, **kwargs):
        Headers = kwargs.get('Headers', {})
        lang = arguments.get('lang', [self._defaultLanguage])[0]

        if Headers and 'Cookie' in Headers and 'user' not in session:
            for cookie in Headers.get('Cookie','').split(';'):
                name, value = cookie.strip().split("=", 1)
                if name == self._rememberMeCookieName:
                    user = self._rememberMeCookieMethod(value)
                    if user:
                        session['user'] = user
                        break

        if 'user' in session or \
                path == self._loginPath or \
                any(path.startswith(excluded) for excluded in self._excluding):
            yield self.all.handleRequest(session=session, path=path, query=query, arguments=arguments, **kwargs)
            return
        session[ORIGINAL_PATH] = '%s%s' % (path, "?%s" % query if query else "")
        session['BasicHtmlLoginForm.formValues'] = {'errorMessage': getLabel(lang=lang, form='errorMessage', key='loginRequiredFor').format(path)}
        yield redirectHttp % self._loginPath

ORIGINAL_PATH = 'originalPath'
