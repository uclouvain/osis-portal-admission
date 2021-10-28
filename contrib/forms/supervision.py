# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.actor import ActorType


class DoctorateAdmissionSupervisionForm(forms.Form):
    type = forms.ChoiceField(
        label="",
        choices=ActorType.choices(),
        widget=forms.RadioSelect(),
    )
    tutor = forms.CharField(
        label=_("Search a tutor by name"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:tutor"),
        required=False,
    )
    person = forms.CharField(
        label=_("Search a person by name"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:person"),
        required=False,
    )

    def clean(self):
        data = self.cleaned_data
        if data['type'] == ActorType.CA_MEMBER.name:
            if not data['person']:
                self.add_error('person', _("This field is required"))
        else:
            if not data['tutor']:
                self.add_error('tutor', _("This field is required"))
        return super().clean()

    class Media:
        js = ('dependsOn.min.js',)
