## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

def getLabel(lang, form, key):
    return LABELS[form][key][lang]

LABELS = {
    "objectRegistry": {
        "unexistingIdentifier": dict(en="Identifier '{identifier}' does not exist.", nl="Identifier '{identifier}' bestaat niet."),
        "existingIdentifier": dict(en="Identifier '{identifier}' already exists.", nl="Identifier '{identifier}' bestaat al."),
        "badIdentifier": dict(en="'{identifier}' is not a valid UUID.", nl="'{identifier}' is geen geldige UUID."),
        "unexpectedException": dict(en='Something bad happened: "{0}".', nl="Er is iets misgegaan \"{0}\".")
    },
}
