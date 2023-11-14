# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from functools import partial

from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from admission.contrib.forms import AdmissionFileUploadField as FileUploadField
from admission.utils import mark_safe_lazy

BooleanRadioSelect = partial(
    forms.RadioSelect,
    choices=((True, _("Yes")), (False, _("No"))),
    attrs={'autocomplete': "off"},
)


class PoolQuestionsForm(forms.Form):
    is_belgian_bachelor = forms.NullBooleanField(
        label=_(
            "Are you currently enrolled in the first year of a bachelor's degree at a French Community "
            "of Belgium haute ecole or university?"
        ),
        widget=BooleanRadioSelect(),
        required=False,
    )
    is_external_reorientation = forms.NullBooleanField(
        label=mark_safe_lazy(
            _(
                'Would you like to switch courses this academic year at UCLouvain? '
                '(<a href="%(url)s" target="_blank">Informations</a>)'
            ),
            url='https://uclouvain.be/fr/etudier/inscriptions/suivi-particulier.html#r%C3%A9orientation',
        ),
        widget=BooleanRadioSelect(),
        required=False,
    )
    regular_registration_proof = FileUploadField(max_files=1, required=False)
    is_external_modification = forms.NullBooleanField(
        label=mark_safe_lazy(
            _(
                "Would you like to change your UCLouvain enrolment for this academic year? "
                '(<a href="%(url)s" target="_blank">Informations</a>)'
            ),
            url='https://uclouvain.be/fr/etudier/inscriptions/suivi-particulier.html#modificationinscr',
        ),
        widget=BooleanRadioSelect(),
        required=False,
    )
    registration_change_form = FileUploadField(max_files=1, required=False)
    is_non_resident = forms.NullBooleanField(
        label=_("You are applying as ..."),
        widget=forms.RadioSelect(
            choices=(
                (False, _("Resident (as defined by government decree)")),
                (True, _("Non-resident (as defined by government decree)")),
            ),
            attrs={'autocomplete': "off"},
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.initial['modification_pool_end_date'] is not None:
            date: datetime.datetime = self.initial['modification_pool_end_date']
            label = format_html(
                _(
                    '<a href="{url}" target=_blank">Change of enrolment form</a>, '
                    'duly completed and accompanied by the mentioned annexes'
                ),
                url=(
                    'https://cdn.uclouvain.be/groups/cms-editors-sic/sic/public/inscriptions/'
                    f'{date.year}/Formulaire%20de%20modification%20-%20BAC1%20-%20Externe%20vers%20l%27'
                    f'UCLouvain_{date.year - 2000}-{date.year - 1999}.pdf'
                ),
            )
            self.fields['registration_change_form'].label = label

        elif self.initial['reorientation_pool_end_date'] is not None:
            date: datetime.datetime = self.initial['reorientation_pool_end_date']
            self.fields['regular_registration_proof'].label = _(
                'Certificate of regular enrolment for the %(year)s academic year from the establishment in '
                'which you are currently enrolled (dated no earlier than 1 November)'
            ) % {'year': f"{date.year - 1}-{date.year}"}

        # Remove fields that are not returned pool_questions
        requested_field_names = list(kwargs['initial'].keys())
        for field_name in [f for f in self.fields if f not in requested_field_names]:
            del self.fields[field_name]

    def clean(self):
        data = super().clean()

        if 'is_non_resident' in self.fields and data['is_non_resident'] is None:
            self.add_error('is_non_resident', self.fields['is_non_resident'].error_messages['required'])

        if data.get('is_belgian_bachelor') is False and self.initial['modification_pool_end_date']:
            # not belgian bachelor, clean modification fields
            data['is_external_modification'] = False
            data['registration_change_form'] = []

        elif data.get('is_belgian_bachelor') is False and self.initial['reorientation_pool_end_date']:
            # not belgian bachelor, clean reorientation fields
            data['is_external_reorientation'] = False
            data['regular_registration_proof'] = []

        elif (
            'is_belgian_bachelor' in data
            and data['is_belgian_bachelor'] is None
            and data.get('is_non_resident') is not True
            and (self.initial['modification_pool_end_date'] or self.initial['reorientation_pool_end_date'])
        ):
            # no belgian bachelor, modification asked
            self.add_error(
                'is_belgian_bachelor',
                self.fields['is_belgian_bachelor'].error_messages['required'],
            )

        elif data.get('is_belgian_bachelor') is True and self.initial['modification_pool_end_date']:
            # belgian bachelor, modification asked
            if data.get('is_external_modification') is None:
                self.add_error(
                    'is_external_modification',
                    self.fields['is_external_modification'].error_messages['required'],
                )
            elif not data['is_external_modification']:
                data['registration_change_form'] = []

        elif data.get('is_belgian_bachelor') is True and self.initial['reorientation_pool_end_date']:
            # belgian bachelor, reorientation asked
            if data.get('is_external_reorientation') is None:
                self.add_error(
                    'is_external_reorientation',
                    self.fields['is_external_reorientation'].error_messages['required'],
                )
            elif not data['is_external_reorientation']:
                data['regular_registration_proof'] = []

        return data

    class Media:
        js = ['js/dependsOn.min.js']
