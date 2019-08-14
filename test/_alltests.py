#!/usr/bin/env python
## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2008-2009 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2012-2019 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
# Copyright (C) 2018 SURF https://surf.nl
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

from os import system                            #DO_NOT_DISTRIBUTE
system('find .. -name "*.pyc" | xargs rm -f')    #DO_NOT_DISTRIBUTE
from seecrdeps import includeParentAndDeps       #DO_NOT_DISTRIBUTE
includeParentAndDeps(__file__, scanForDeps=True) #DO_NOT_DISTRIBUTE

from unittest import main

from dynamichtmltest import DynamicHtmlTest
from errorlogtest import ErrorLogTest
from htmltest import HtmlTest
from tagtest import TagTest
from objectregistrytest import ObjectRegistryTest
from postactionstest import PostActionsTest
from urlencodetest import UrlencodeTest
from nextpreviteratortest import NextPrevIteratorTest

from login.basichtmlloginformtest import BasicHtmlLoginFormTest
from login.groupsfiletest import GroupsFileTest
from login.passwordfiletest import PasswordFileTest
from login.remembermecookietest import RememberMeCookieTest
from login.securezonetest import SecureZoneTest
from login.usergroupsformtest import UserGroupsFormTest
from login.userinfotest import UserInfoTest
from login.userinfoformtest import UserInfoFormTest

from tools.htmltotagtest import HtmlToTagTest

if __name__ == '__main__':
    main()
