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

def getLabel(lang, form, key):
    return LABELS[form][key][lang]

LABELS = {
    'loginForm': {
        'username': dict(en='Username', nl='Gebruikersnaam'),
        'password': dict(en='Password', nl='Wachtwoord'),
        'login': dict(en='Login', nl="Inloggen"),
        'invalid': dict(en='Invalid username or password', nl='Ongeldige gebruikersnaam of wachtwoord'),
        'rememberMe': dict(en="Remember me", nl="Vergeet-me-niet"),
    },
    'changepasswordForm': {
        'old-password': dict(en="Old password", nl="Oud wachtwoord"),
        'new-password': dict(en='New password', nl="Nieuw wachtwoord"),
        'new-password-repeat': dict(en="Retype new password", nl="Herhaal nieuw wachtwoord"),
        'change': dict(en="Change", nl="Aanpassen"),
        'dontMatch': dict(en="New passwords do not match", nl="Nieuwe wachtwoorden komen niet overeen"),
        'usernamePasswordDontMatch': dict(en="Username and password do not match", nl="Gebruikersnaam en wachtwoord komen niet overeen")
    },
    'newuserForm': {
        'username': dict(en='Username', nl='Gebruikersnaam'),
        'password': dict(en='Password', nl='Wachtwoord'),
        'password-repeat': dict(en="Retype password", nl="Herhaal wachtwoord"),
        'create': dict(en="Create", nl="Aanmaken"),
        'dontMatch': dict(en="Passwords do not match", nl="Wachtwoorden komen niet overeen"),
        'added': dict(en="Added user", nl="Gebruiker toegevoegd")
    },
    'errorMessage': {
        'loginRequiredFor': dict(en='Login required for "{0}".', nl='Inloggen verplicht voor "{0}".')
    },
    'removeUserForm': {
        'notExists': dict(en="User \"%s\" does not exist", nl="Gebruiker \"%s\" bestaat niet")
    }
}
