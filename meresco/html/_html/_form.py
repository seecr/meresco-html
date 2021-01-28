## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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

from ._html import Html

class HtmlForm(Html):
    def __init__(self, action):
        Html.__init__(self)
        self.action = action
        self._formGroups = []

    def main(self, **kwargs):
        with self.form_tag(**kwargs):
            yield self.hidden_input(**kwargs)
            for formGroup in self._formGroups:
               yield formGroup.main(**kwargs)

    def form_tag(self, *args, **kwargs):
        return self.tag('form', action=self.action, method="POST", role="form")

    def hidden_input(self, hiddenData=None, **kwargs):
        hiddenData = hiddenData or {}
        for name, value in list(hiddenData.items()):
            with self.tag('input').set('type', 'hidden')\
                .set('name', name)\
                .set('value', value):
                yield ''

    def addFormGroup(self, formGroup):
        self._formGroups.append(formGroup.setForm(self))

