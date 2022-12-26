# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.utils.safestring import mark_safe


class CharFieldCheckbox(forms.CheckboxSelectMultiple):
    """Widget to pass the value of the checkbox (which CheckboxInput does not do)"""

    def use_required_attribute(self, initial):
        # We know we have only one checkbox, and it must be required
        return True


class AdmissionConfirmSubmitForm(forms.Form):
    pool = forms.CharField(widget=forms.HiddenInput())
    annee = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, elements, **kwargs):
        super().__init__(*args, **kwargs)
        if not elements:
            return

        for element in elements:
            if element['type'] == 'checkbox':
                self.fields[element['nom']] = forms.MultipleChoiceField(
                    choices=[(element['texte'], mark_safe(element['texte']))],
                    label=element['titre'],
                    widget=CharFieldCheckbox(
                        attrs={'autocomplete': "off"},
                    ),
                )
            else:
                self.fields[element['nom']] = forms.CharField(
                    label=element['titre'],
                    widget=forms.RadioSelect(
                        choices=[(f"{r} {element['texte']}", r) for r in element['reponses']],
                        attrs={'autocomplete': "off"},
                    ),
                    help_text=element['texte'],
                )

    def clean(self):
        data = super().clean()
        for field_name in data:
            # Flatten values
            if isinstance(data.get(field_name), list):
                data[field_name] = data[field_name][0]
        return data
