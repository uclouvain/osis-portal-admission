# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict, Optional

from dal import forward
from django import forms
from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from waffle import switch_is_active

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    TRAINING_TYPES_WITH_SCHOLARSHIP,
    AdmissionType,
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.state_iufc import StateIUFC
from admission.contrib.enums.training_choice import (
    ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE,
    ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE,
    TYPES_FORMATION_GENERALE,
    TypeFormation,
    TypeFormationChoisissable,
)
from admission.contrib.enums.ways_find_out_about_the_course import (
    ChoixMoyensDecouverteFormation,
)
from admission.contrib.forms import (
    EMPTY_CHOICE,
    EMPTY_VALUE,
    RadioBooleanField,
    autocomplete,
    get_campus_choices,
)
from admission.contrib.forms.project import (
    COMMISSION_CDSS,
    COMMISSIONS_CDE_CLSM,
    SCIENCE_DOCTORATE,
)
from admission.contrib.forms.specific_question import ConfigurableFormMixin
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.continuing_education import ContinuingEducationService
from admission.services.education_group import TrainingsService
from admission.services.proposition import AdmissionPropositionService
from admission.utils import format_scholarship, split_training_id
from reference.services.scholarship import ScholarshipService


def get_training(person, training: str):
    groups = split_training_id(training)
    if len(groups) == 2:
        return TrainingsService.get_training(person=person, acronym=groups[0], year=groups[1]).to_dict()


def get_training_choices(training):
    return [
        (
            "{acronym}-{academic_year}".format(
                acronym=training['acronym'],
                academic_year=int(training['academic_year']),
            ),
            '{name} ({campus}) <span class="training-acronym">{acronym}</span>'.format(
                name=training['title'] if get_language() == settings.LANGUAGE_CODE else training['title_en'],
                campus=training['main_teaching_campus'].get('name'),
                acronym=training['acronym'],
            ),
        )
    ]


class TrainingChoiceForm(ConfigurableFormMixin):
    NO_VALUE = 'NO'

    training_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + TypeFormationChoisissable.choices(),
        label=_('Course type'),
        required=True,
    )

    campus = forms.ChoiceField(
        initial=EMPTY_VALUE,
        label=_('Campus (optional)'),
        widget=autocomplete.Select2,
        required=False,
    )

    # General education
    general_education_training = forms.CharField(
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:general-education',
            forward=['training_type', 'campus'],
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for your course title using a word from the title (e.g. management)'),
            },
        ),
    )

    # A mix of continuing education and general certificate
    mixed_training = forms.CharField(
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:mixed-training',
            forward=['training_type', 'campus'],
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for your course title using a word from the title (e.g. management)'),
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
                'placeholder': _("Reasons for pre-admission."),
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
        label=pgettext_lazy('admission', 'Course'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:doctorate',
            forward=['sector', 'campus'],
            attrs={
                'data-html': True,
                'data-placeholder': _('Search for your course title using a word from the title (e.g. management)'),
            },
        ),
    )

    proximity_commission_cde = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDEouCLSM.choices(),
        required=False,
    )

    proximity_commission_cdss = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixCommissionProximiteCDSS.choices(),
        required=False,
    )

    science_sub_domain = forms.ChoiceField(
        label=_("Proximity commission / Subdomain"),
        choices=EMPTY_CHOICE + ChoixSousDomaineSciences.choices(),
        required=False,
    )

    related_pre_admission = forms.ChoiceField(
        label=_("Would you like to create an admission request following a pre-admission request?"),
        choices=[[NO_VALUE, _('No')]],
        required=False,
        widget=forms.RadioSelect,
    )

    # Continuing education
    motivations = forms.CharField(
        label=_('Motivations'),
        widget=forms.Textarea(
            attrs={
                'rows': 6,
            }
        ),
        max_length=1000,
        required=False,
    )

    ways_to_find_out_about_the_course = forms.MultipleChoiceField(
        label=_('How did you hear about this course?'),
        required=False,
        choices=ChoixMoyensDecouverteFormation.choices(),
        widget=forms.CheckboxSelectMultiple,
    )

    other_way_to_find_out_about_the_course = forms.CharField(
        label='',
        max_length=1000,
        required=False,
        widget=forms.TextInput(
            attrs={
                'aria-label': _('How else did you hear about this course?'),
            },
        ),
    )

    interested_mark = forms.NullBooleanField(
        label=_('Yes, I am interested in this course'),
        required=False,
        widget=forms.CheckboxInput,
    )

    # Scholarship

    has_double_degree_scholarship = RadioBooleanField(
        label=_('Are you a dual degree student?'),
        required=False,
        help_text=_(
            'Dual degrees involve joint coursework between two or more universities, leading to two separate diplomas '
            'awarded by each signatory university.'
        ),
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
        help_text=_(
            'An international scholarship may be awarded to students as part of a project. These international '
            'grants are awarded by ARES and a scholarship certificate must be provided.'
        ),
    )

    international_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.BOURSE_INTERNATIONALE_FORMATION_GENERALE.name, 'scholarship_type')],
        ),
    )

    has_erasmus_mundus_scholarship = RadioBooleanField(
        label=_('Are you an Erasmus Mundus student?'),
        required=False,
        help_text=_(
            'Erasmus Mundus is a study abroad programme devised by an international partnership of higher '
            'education institutions. Scholarships are awarded to students and proof of funding is therefore required.'
        ),
    )

    erasmus_mundus_scholarship = forms.CharField(
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:scholarship',
            forward=[forward.Const(TypeBourse.ERASMUS_MUNDUS.name, 'scholarship_type')],
        ),
    )

    def __init__(self, person, current_context, *args, **kwargs):
        self.person = person
        self.current_context = current_context
        self.admission_uuid = kwargs.pop('admission_uuid', None)
        self.pre_admissions: Dict[str, Dict] = {}

        super().__init__(*args, **kwargs)

        if not switch_is_active('admission-doctorat'):
            self.fields['training_type'].choices = tuple(
                choice
                for choice in self.fields['training_type'].choices
                if choice[0] != TypeFormationChoisissable.DOCTORAT.name
            )

        general_education_training = self.data.get(
            self.add_prefix('general_education_training'),
            self.initial.get('general_education_training') if not self.is_bound else '',
        )
        mixed_training = self.data.get(
            self.add_prefix('mixed_training'),
            self.initial.get('mixed_training') if not self.is_bound else '',
        )
        doctorate_training = self.data.get(
            self.add_prefix('doctorate_training'),
            self.initial.get('doctorate_training') if not self.is_bound else '',
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

        if general_education_training:
            self.general_education_training_obj = get_training(
                person=self.person,
                training=general_education_training,
            )
            general_choices = get_training_choices(training=self.general_education_training_obj)

            # We need to provide additional data so we use the data attribute instead of the choice
            self.fields['general_education_training'].widget.attrs['data-data'] = json.dumps(
                [
                    {
                        'id': general_choices[0][0],
                        'text': general_choices[0][1],
                        'domain_code': self.general_education_training_obj['domain_code'],
                        'training_type': self.general_education_training_obj['education_group_type'],
                    }
                ]
            )
            self.fields['training_type'].initial = ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(
                self.general_education_training_obj.get('education_group_type')
            )
        elif mixed_training:
            training = get_training(person=self.person, training=mixed_training)
            self.fields['mixed_training'].widget.choices = get_training_choices(
                training=training,
            )
            self.fields['training_type'].initial = TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name
            # Determine real type
            training_type = ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE[training['education_group_type']]
            if training_type == TypeFormation.FORMATION_CONTINUE.name:
                self.continuing_education_training_obj = training
            else:
                self.general_education_training_obj = training
            # Provide additional data used in the template
            self.fields['mixed_training'].training_type = training['education_group_type']

        elif doctorate_training:
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

            self.fields['training_type'].initial = ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(
                self.doctorate_training_obj.get('education_group_type')
            )

            # Initialize the right proximity commission field
            if self.initial.get('proximity_commission'):
                if self.doctorate_training_obj['management_entity'] in COMMISSIONS_CDE_CLSM:
                    self.fields['proximity_commission_cde'].initial = self.initial['proximity_commission']
                elif self.doctorate_training_obj['management_entity'] == COMMISSION_CDSS:
                    self.fields['proximity_commission_cdss'].initial = self.initial['proximity_commission']
                elif self.doctorate_training_obj['acronym'] == SCIENCE_DOCTORATE:
                    self.fields['science_sub_domain'].initial = self.initial['proximity_commission']

        for scholarship_name, scholarship_uuid in scholarships.items():
            if scholarship_uuid:
                scholarship_obj = ScholarshipService.get_scholarship(
                    person=person,
                    scholarship_uuid=scholarship_uuid,
                )
                self.fields[scholarship_name].widget.choices = (
                    (
                        scholarship_obj.uuid,
                        format_scholarship(scholarship_obj),
                    ),
                )

        self.fields['sector'].widget.choices = EMPTY_CHOICE + tuple(
            (sector.sigle, f"{sector.sigle} - {sector.intitule}")
            for sector in AdmissionAutocompleteService.get_sectors(person)
        )

        self.initialize_pre_admission_field()

    def _format_pre_admission_training(self, training):
        return f"{training.sigle} - {training.intitule} ({training.campus.nom})"

    def initialize_pre_admission_field(self):
        # Manage a doctorate admission following a pre-admission
        if self.current_context == 'create':
            doctorate_pre_admissions = AdmissionPropositionService.get_doctorate_pre_admission_propositions(self.person)

            self.fields['related_pre_admission'].choices = [[self.NO_VALUE, _('No')]]

            for doctorate_pre_admission in doctorate_pre_admissions:
                self.pre_admissions[doctorate_pre_admission.uuid] = doctorate_pre_admission.to_dict()
                self.fields['related_pre_admission'].choices.append(
                    [
                        doctorate_pre_admission.uuid,
                        _('Yes, for the doctorate %(doctorate_name)s')
                        % {'doctorate_name': self._format_pre_admission_training(doctorate_pre_admission.doctorat)},
                    ]
                )

        self.fields['related_pre_admission'].disabled = not bool(self.pre_admissions)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('training_type'):
            return

        # If changing context after creation, raise an error
        if self.current_context != 'create':
            training = (
                cleaned_data.get('general_education_training')
                or cleaned_data.get('mixed_training')
                or cleaned_data.get('doctorate_training')
            )
            if training:
                training = get_training(person=self.person, training=training)
                if self.current_context != ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE[training['education_group_type']]:
                    msg = _(
                        'To choose this course, you need to <a href="%(url)s">cancel</a> '
                        'your application and create a new one.'
                    )
                    url = resolve_url(f'admission:{self.current_context}:cancel', pk=self.admission_uuid)
                    raise forms.ValidationError(mark_safe(msg % {'url': url}))

        # Determine real training type
        if cleaned_data.get('training_type') == TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name:
            training = get_training(person=self.person, training=cleaned_data['mixed_training'])

            if training:
                cleaned_data['training_type'] = ADMISSION_EDUCATION_TYPE_BY_OSIS_TYPE.get(
                    training['education_group_type']
                )
                cleaned_data['general_education_training'] = cleaned_data['mixed_training']
            else:
                self.add_error('mixed_training', FIELD_REQUIRED_MESSAGE)

        training_type = cleaned_data.get('training_type')

        self.clean_doctorate(training_type, cleaned_data)
        self.clean_continuing_education(training_type, cleaned_data)
        self.clean_general_education(training_type, cleaned_data)
        self.clean_scholarships(cleaned_data)

    def clean_scholarships(self, cleaned_data):
        if (
            self.general_education_training_obj
            and self.general_education_training_obj['education_group_type'] in TRAINING_TYPES_WITH_SCHOLARSHIP
        ):
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

            if cleaned_data.get('has_erasmus_mundus_scholarship'):
                if not cleaned_data.get('erasmus_mundus_scholarship'):
                    self.add_error('erasmus_mundus_scholarship', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['erasmus_mundus_scholarship'] = ''

                if cleaned_data.get('has_erasmus_mundus_scholarship') is None:
                    self.add_error('has_erasmus_mundus_scholarship', FIELD_REQUIRED_MESSAGE)

        else:
            cleaned_data['has_double_degree_scholarship'] = None
            cleaned_data['has_international_scholarship'] = None
            cleaned_data['has_erasmus_mundus_scholarship'] = None
            cleaned_data['double_degree_scholarship'] = ''
            cleaned_data['international_scholarship'] = ''
            cleaned_data['erasmus_mundus_scholarship'] = ''

    def clean_general_education(self, training_type, cleaned_data):
        if training_type in TYPES_FORMATION_GENERALE:
            if not cleaned_data.get('general_education_training'):
                self.add_error('general_education_training', FIELD_REQUIRED_MESSAGE)

    def clean_continuing_education(self, training_type, cleaned_data):
        if training_type == TypeFormation.FORMATION_CONTINUE.name:
            if not cleaned_data.get('mixed_training'):
                self.add_error('mixed_training', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('motivations'):
                self.add_error('motivations', FIELD_REQUIRED_MESSAGE)

            if self.continuing_education_training_obj:
                additional_training_information = ContinuingEducationService.get_continuing_education_information(
                    person=self.person,
                    acronym=self.continuing_education_training_obj['acronym'],
                    year=int(self.continuing_education_training_obj['academic_year']),
                )

                if additional_training_information.inscription_au_role_obligatoire:
                    if not cleaned_data.get('ways_to_find_out_about_the_course'):
                        self.add_error('ways_to_find_out_about_the_course', FIELD_REQUIRED_MESSAGE)
                else:
                    cleaned_data['ways_to_find_out_about_the_course'] = []

                if not additional_training_information.etat == StateIUFC.CLOSED.name:
                    cleaned_data['interested_mark'] = None

            else:
                cleaned_data['ways_to_find_out_about_the_course'] = []
                cleaned_data['interested_mark'] = None

            if (
                cleaned_data.get('ways_to_find_out_about_the_course')
                and ChoixMoyensDecouverteFormation.AUTRE.name in cleaned_data['ways_to_find_out_about_the_course']
            ):
                if not cleaned_data.get('other_way_to_find_out_about_the_course'):
                    self.add_error('other_way_to_find_out_about_the_course', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['other_way_to_find_out_about_the_course'] = ''

    def clean_doctorate(self, training_type, cleaned_data):
        if training_type == TypeFormation.DOCTORAT.name:
            sector = cleaned_data.get('sector')
            campus = cleaned_data.get('campus')

            if not cleaned_data.get('admission_type'):
                self.add_error('admission_type', FIELD_REQUIRED_MESSAGE)

            if cleaned_data.get('admission_type') == AdmissionType.PRE_ADMISSION.name:
                if not cleaned_data.get('justification'):
                    self.add_error('justification', FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data['justification'] = ''

            if not sector:
                self.add_error('sector', FIELD_REQUIRED_MESSAGE)

            # Either the related pre admission or the doctorate training is required
            if cleaned_data.get('admission_type') == AdmissionType.ADMISSION.name:
                # The pre admission choices depend on the chosen sector and campus
                pre_admission_choices = {
                    pre_admission['uuid']
                    for pre_admission in self.pre_admissions.values()
                    if pre_admission['code_secteur_formation'] == sector
                    and (not campus or campus == EMPTY_VALUE or pre_admission['doctorat']['campus']['uuid'] == campus)
                }

                related_pre_admission_data = cleaned_data.get('related_pre_admission')
                if pre_admission_choices and related_pre_admission_data != self.NO_VALUE:
                    cleaned_data['doctorate_training'] = ''
                    cleaned_data['proximity_commission_cde'] = ''
                    cleaned_data['proximity_commission_cdss'] = ''
                    cleaned_data['science_sub_domain'] = ''

                    if related_pre_admission_data not in pre_admission_choices:
                        self.add_error('related_pre_admission', FIELD_REQUIRED_MESSAGE)

                    return cleaned_data

            cleaned_data['related_pre_admission'] = ''

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
