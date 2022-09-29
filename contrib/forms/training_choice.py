# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
from typing import Optional

from dal import autocomplete, forward
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _, get_language

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    AdmissionType,
    ChoixProximityCommissionCDE,
    ChoixProximityCommissionCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.training_choice import TypeFormation, TYPES_FORMATION_GENERALE
from admission.contrib.forms import get_campus_choices, EMPTY_CHOICE, RadioBooleanField, EMPTY_VALUE
from admission.contrib.forms.project import COMMISSIONS_CDE_CLSM, COMMISSION_CDSS, SCIENCE_DOCTORATE
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.education_group import TrainingsService
from admission.services.scholarship import AdmissionScholarshipService
from admission.utils import format_scholarship, split_training_id


def get_training(person, training: str):
    groups = split_training_id(training)
    if len(groups) == 2:
        return TrainingsService.get_training(person=person, acronym=groups[0], year=groups[1]).to_dict()


def get_training_choices(training):
    return [
        (
            "{acronym}-{academic_year}".format(
                acronym=training['acronym'], academic_year=int(training['academic_year'])
            ),
            '{name} ({campus}) - {acronym}'.format(
                name=training['title'] if get_language() == settings.LANGUAGE_CODE else training['title_en'],
                campus=training['enrollment_campus'].get('name'),
                acronym=training['acronym'],
            ),
        )
    ]


class TrainingChoiceForm(forms.Form):
    training_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + TypeFormation.choices(),
        label=_('Training type'),
        required=False,
    )

    campus = forms.ChoiceField(
        initial=EMPTY_VALUE,
        label=_('Campus'),
        widget=autocomplete.Select2,
    )

    # General education
    general_education_training = forms.CharField(
        label=_('Training'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:general-education',
            forward=['training_type', 'campus'],
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )

    # Continuing education
    continuing_education_training = forms.CharField(
        label=_('Training'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:continuing-education',
            forward=['campus'],
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )

    # Doctorate
    admission_type = forms.ChoiceField(
        choices=AdmissionType.choices(),
        initial=AdmissionType.ADMISSION.name,
        label=_('Admission type'),
        required=False,
        widget=forms.RadioSelect,
    )

    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': _("Detail here the reasons which justify the recourse to a provisory admission."),
            }
        ),
        required=False,
    )

    sector = forms.CharField(
        label=_('Sector'),
        required=False,
        widget=autocomplete.Select2(),
    )

    doctorate_training = forms.CharField(
        label=_('Training'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:doctorate',
            forward=['sector', 'campus'],
        ),
    )

    proximity_commission_cde = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixProximityCommissionCDE.choices(),
        required=False,
    )

    proximity_commission_cdss = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixProximityCommissionCDSS.choices(),
        required=False,
    )

    science_sub_domain = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixSousDomaineSciences.choices(),
        required=False,
    )

    # Scholarship

    has_double_degree_scholarship = RadioBooleanField(
        label=_('Are you a double degree student?'),
        required=False,
    )

    double_degree_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.DOUBLE_TRIPLE_DIPLOMATION.name, 'scholarship_type')],
        ),
    )

    has_international_scholarship = RadioBooleanField(
        label=_('Do you have an international scholarship?'),
        required=False,
    )

    international_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name, 'scholarship_type')],
        ),
    )

    has_erasmus_mundus_scholarship = RadioBooleanField(
        label=_('Are you an erasmus mundus student?'),
        required=False,
    )

    erasmus_mundus_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.ERASMUS_MUNDUS.name, 'scholarship_type')],
        ),
    )

    def __init__(self, person, on_update=False, **kwargs):
        self.person = person
        self.on_update = on_update

        super().__init__(**kwargs)

        training_type = self.data.get(
            self.add_prefix('training_type'),
            self.initial.get('training_type'),
        )

        general_education_training = self.data.get(
            self.add_prefix('general_education_training'),
            self.initial.get('general_education_training'),
        )
        continuing_education_training = self.data.get(
            self.add_prefix('continuing_education_training'),
            self.initial.get('continuing_education_training'),
        )

        doctorate_training = self.data.get(
            self.add_prefix('doctorate_training'),
            self.initial.get('doctorate_training'),
        )

        scholarships = {
            'double_degree_scholarship': self.data.get(
                self.add_prefix('double_degree_scholarship'),
                self.initial.get('double_degree_scholarship'),
            ),
            'international_scholarship': self.data.get(
                self.add_prefix('international_scholarship'),
                self.initial.get('international_scholarship'),
            ),
            'erasmus_mundus_scholarship': self.data.get(
                self.add_prefix('erasmus_mundus_scholarship'),
                self.initial.get('erasmus_mundus_scholarship'),
            ),
        }

        # Initialize fields with dynamic choices
        self.fields['campus'].choices = get_campus_choices(self.person)

        self.general_education_training_obj: Optional[dict] = None
        self.continuing_education_training_obj: Optional[dict] = None
        self.doctorate_training_obj: Optional[dict] = None

        if training_type:
            if general_education_training and training_type in TYPES_FORMATION_GENERALE:
                self.general_education_training_obj = get_training(
                    person=self.person, training=general_education_training,
                )
                self.fields['general_education_training'].widget.choices = get_training_choices(
                    training=self.general_education_training_obj,
                )
            elif continuing_education_training and training_type == TypeFormation.FORMATION_CONTINUE.name:
                self.continuing_education_training_obj = get_training(
                    person=self.person, training=continuing_education_training,
                )
                self.fields['continuing_education_training'].widget.choices = get_training_choices(
                    training=self.continuing_education_training_obj,
                )
            elif doctorate_training and training_type == TypeFormation.DOCTORAT.name:
                self.doctorate_training_obj = get_training(person=self.person, training=doctorate_training)
                doctorate_choices = get_training_choices(training=self.doctorate_training_obj)

                # We need to provide additional data so we use the data attribute instead of the choice
                self.fields['doctorate_training'].widget.attrs['data-data'] = json.dumps(
                    [
                        {
                            'id': doctorate_choices[0][0],
                            'sigle': self.doctorate_training_obj['acronym'],
                            'sigle_entite_gestion': self.doctorate_training_obj['management_entity'],
                            'text': doctorate_choices[0][1],
                        }
                    ]
                )

                # Initialize the right proximity commission field
                if self.initial.get('proximity_commission'):
                    if self.doctorate_training_obj['management_entity'] in COMMISSIONS_CDE_CLSM:
                        self.initial['proximity_commission_cde'] = self.initial['proximity_commission']
                    elif self.doctorate_training_obj['management_entity'] == COMMISSION_CDSS:
                        self.initial['proximity_commission_cdss'] = self.initial['proximity_commission']
                    elif self.doctorate_training_obj['acronym'] == SCIENCE_DOCTORATE:
                        self.initial['science_sub_domain'] = self.initial['proximity_commission']

        self.fields['sector'].widget.choices = EMPTY_CHOICE + tuple(
            (sector.sigle, f"{sector.sigle} - {sector.intitule}")
            for sector in AdmissionAutocompleteService.get_sectors(person)
        )

        for scholarship_name, scholarship_uuid in scholarships.items():
            if scholarship_uuid:
                scholarship_obj = AdmissionScholarshipService.get_scholarship(
                    person=person,
                    scholarship_uuid=scholarship_uuid,
                )
                self.fields[scholarship_name].widget.choices = (
                    (scholarship_obj.uuid, format_scholarship(scholarship_obj),),
                )

        # Specificities on update -> Some fields can not be updated
        if self.on_update:
            disabled_fields_on_create = [
                # All trainings
                'training_type',
                # Doctorate
                'proximity_commission_cde',
                'proximity_commission_cdss',
                'science_sub_domain',
                'sector',
                'doctorate_training',
            ]

            for field in disabled_fields_on_create:
                self.fields[field].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        training_type = cleaned_data.get('training_type')

        if not self.on_update and not training_type:
            self.add_error('training_type', FIELD_REQUIRED_MESSAGE)

        if cleaned_data.get('campus') == EMPTY_VALUE:
            cleaned_data['campus'] = ''

        self.clean_doctorate(training_type, cleaned_data)

        self.clean_continuing_education(training_type, cleaned_data)

        self.clean_erasmus_scholarship(training_type, cleaned_data)

        self.clean_general_education(training_type, cleaned_data)

        self.clean_master_scholarships(training_type, cleaned_data)

    def clean_master_scholarships(self, training_type, cleaned_data):
        if training_type == TypeFormation.MASTER.name:
            if cleaned_data.get('has_double_degree_scholarship'):
                if not cleaned_data.get('double_degree_scholarship'):
                    self.add_error('double_degree_scholarship', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['double_degree_scholarship'] = ''

                if cleaned_data.get('has_double_degree_scholarship') is None:
                    self.add_error('has_double_degree_scholarship', FIELD_REQUIRED_MESSAGE)

            if cleaned_data.get('has_international_scholarship'):
                if not cleaned_data.get('international_scholarship'):
                    self.add_error('international_scholarship', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['international_scholarship'] = ''

                if cleaned_data.get('has_international_scholarship') is None:
                    self.add_error('has_international_scholarship', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['has_double_degree_scholarship'] = ''
            cleaned_data['has_international_scholarship'] = ''
            cleaned_data['double_degree_scholarship'] = ''
            cleaned_data['international_scholarship'] = ''

    def clean_erasmus_scholarship(self, training_type, cleaned_data):
        if training_type in TYPES_FORMATION_GENERALE or training_type == TypeFormation.DOCTORAT.name:
            if cleaned_data.get('has_erasmus_mundus_scholarship'):
                if not cleaned_data.get('erasmus_mundus_scholarship'):
                    self.add_error('erasmus_mundus_scholarship', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['erasmus_mundus_scholarship'] = ''

                if cleaned_data.get('has_erasmus_mundus_scholarship') is None:
                    self.add_error('has_erasmus_mundus_scholarship', FIELD_REQUIRED_MESSAGE)

    def clean_general_education(self, training_type, cleaned_data):
        if training_type in TYPES_FORMATION_GENERALE:
            if not cleaned_data.get('general_education_training'):
                self.add_error('general_education_training', FIELD_REQUIRED_MESSAGE)

    def clean_continuing_education(self, training_type, cleaned_data):
        if training_type == TypeFormation.FORMATION_CONTINUE.name:
            if not cleaned_data.get('continuing_education_training'):
                self.add_error('continuing_education_training', FIELD_REQUIRED_MESSAGE)

    def clean_doctorate(self, training_type, cleaned_data):
        if training_type == TypeFormation.DOCTORAT.name:
            if not cleaned_data.get('admission_type'):
                self.add_error('admission_type', FIELD_REQUIRED_MESSAGE)

            if cleaned_data.get('admission_type') == AdmissionType.PRE_ADMISSION.name:
                if not cleaned_data.get('justification'):
                    self.add_error('justification', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['justification'] = ''

            if not cleaned_data.get('sector'):
                self.add_error('sector', FIELD_REQUIRED_MESSAGE)

            if not cleaned_data.get('doctorate_training'):
                self.add_error('doctorate_training', FIELD_REQUIRED_MESSAGE)

            if self.doctorate_training_obj and self.doctorate_training_obj['management_entity'] in COMMISSIONS_CDE_CLSM:
                if not cleaned_data.get('proximity_commission_cde'):
                    self.add_error('proximity_commission_cde', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['proximity_commission_cde'] = ''

            if self.doctorate_training_obj and self.doctorate_training_obj['management_entity'] == COMMISSION_CDSS:
                if not cleaned_data.get('proximity_commission_cdss'):
                    self.add_error('proximity_commission_cdss', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['proximity_commission_cdss'] = ''

            if self.doctorate_training_obj and self.doctorate_training_obj['acronym'] == SCIENCE_DOCTORATE:
                if not cleaned_data.get('science_sub_domain'):
                    self.add_error('science_sub_domain', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['science_sub_domain'] = ''

    class Media:
        js = ('js/dependsOn.min.js',)
