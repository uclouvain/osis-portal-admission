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
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.forms import AdmissionFileUploadField as FileUploadField


class DoctorateAdmissionCotutelleForm(forms.Form):
    cotutelle = forms.ChoiceField(
        label=_("Would you like to carry out your thesis under joint supervision with another institution?"),
        choices=[
            ('YES', _("Yes")),
            ('NO', _("No")),
        ],
        widget=forms.RadioSelect,
    )
    motivation = forms.CharField(
        label=_("Motivation for joint supervision"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    institution_fwb = forms.NullBooleanField(
        label=_("Is it a Wallonia-Brussels Federation institution?"),
        required=False,
        widget=forms.RadioSelect(
            choices=(
                ('true', _('Yes')),
                ('false', _('No')),
            ),
        ),
    )
    institution = forms.CharField(
        label=_("Partner institution"),
        required=False,
    )
    demande_ouverture = FileUploadField(
        label=_("Joint supervision request"),
        required=False,
        max_files=1,
        help_text=_("Please complete the \"Application for a cotutelle\" form (available here) and upload it here."),
    )
    convention = FileUploadField(
        label=_("Joint supervision agreement"),
        required=False,
        max_files=1,
    )
    autres_documents = FileUploadField(
        label=_("Other documents relating to joint supervision"),
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("cotutelle") == "YES":
            for field in ['motivation', 'institution', 'demande_ouverture']:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            if cleaned_data.get('institution_fwb') is None:
                self.add_error('institution_fwb', FIELD_REQUIRED_MESSAGE)

        return cleaned_data
