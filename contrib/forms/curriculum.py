# ##############################################################################
# 
#     OSIS stands for Open Student Information System. It's an application
#     designed to manage the core business of higher education institutions,
#     such as universities, faculties, institutes and professional schools.
#     The core business involves the administration of students, teachers,
#     courses, programs and so on.
# 
#     Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     A copy of this license - GNU General Public License - is available
#     at the root of the source code of this program.  If not,
#     see http://www.gnu.org/licenses/.
# 
# ##############################################################################
from dal import autocomplete, forward
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.curriculum import *
from admission.contrib.enums.secondary_studies import BelgianCommunitiesOfEducation
from admission.contrib.forms import EMPTY_CHOICE, get_country_initial_choices, get_academic_year_initial_choices, \
    EMPTY_CHOICE_LIST, CustomDateInput
from admission.services.reference import AcademicYearService
from osis_document.contrib.forms import FileUploadField


class DoctorateAdmissionCurriculumExperienceForm(forms.Form):
    # Common
    academic_year = forms.ChoiceField(
        label=_("Academic year"),
    )
    type = forms.ChoiceField(
        label=_("Type"),
        choices=ExperienceType.choices(),
        widget=forms.RadioSelect,
    )
    country = forms.CharField(
        label=_("Country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    institute_name = forms.CharField(
        label=_("Institute name"),
        required=False,
    )
    institute_city_be = forms.CharField(
        label=_("Institute city"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:city",
            forward=(forward.Field('institute_postal_code', 'postal_code'),),
        ),
    )
    institute_city = forms.CharField(
        label=_("Institute city"),
        required=False,
    )
    # Common university higher education
    institute = forms.CharField(
        label=_("Institute"),
        required=False,
        empty_value=None,
        # TODO add autocomplete
    )
    institute_not_found = forms.BooleanField(
        label=_("I don't find my institute in the list."),
        required=False,
    )
    institute_postal_code = forms.CharField(
        label=_("Institute postal code"),
        required=False,
    )
    education_name = forms.CharField(
        label=_("Name of the diploma or of the education"),
        required=False,
    )
    result = forms.ChoiceField(
        label=_("Result"),
        required=False,
        choices=EMPTY_CHOICE + Result.choices(),
    )
    graduation_year = forms.BooleanField(
        label=_('Is it your graduation year?'),
        required=False,
    )
    obtained_grade = forms.ChoiceField(
        label=_('Obtained grade'),
        choices=EMPTY_CHOICE + Grade.choices(),
        required=False,
    )
    rank_in_diploma = forms.CharField(
        label=_('Rank in diploma'),
        required=False,
    )
    issue_diploma_date = forms.DateField(
        label=_('Issue diploma date'),
        required=False,
        widget=CustomDateInput()
    )
    credit_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + CreditType.choices(),
        label=_('Credit type'),
        required=False,
    )
    entered_credits_number = forms.IntegerField(
        label=_('Entered credit number'),
        min_value=0,
        required=False,
    )
    acquired_credits_number = forms.IntegerField(
        label=_('Acquired credit number'),
        min_value=0,
        required=False,
    )
    transcript = FileUploadField(
        label=_('Transcript'),
        required=False,
    )
    graduate_degree = FileUploadField(
        label=_('Graduate degree'),
        required=False,
    )
    access_certificate_after_60_master = FileUploadField(
        label=_('Access certificate after a 60 master'),
        required=False,
    )
    dissertation_title = forms.CharField(
        label=_('Dissertation title'),
        required=False,
    )
    dissertation_score = forms.DecimalField(
        decimal_places=2,
        label=_('Dissertation score'),
        max_digits=4,
        required=False,
    )
    dissertation_summary = FileUploadField(
        label=_('Dissertation summary'),
        required=False,
    )
    # Belgian higher education
    belgian_education_community = forms.ChoiceField(
        choices=BelgianCommunitiesOfEducation.choices(),
        label=_("Education community"),
        required=False,
        widget=forms.RadioSelect,
    )
    program = forms.CharField(
        label=_("Program"),
        required=False,
        empty_value=None,
        # TODO Add autocomplete
    )
    program_not_found = forms.BooleanField(
        label=_("I don't find my program in the list."),
        required=False,
    )
    other_program = forms.CharField(
        label=_("Other program"),
        required=False,
    )
    study_system = forms.ChoiceField(
        choices=EMPTY_CHOICE + StudySystem.choices(),
        label=_("Study system"),
        required=False,
    )
    curriculum = FileUploadField(
        help_text=_('Must be detailed, dated and signed.'),
        label=_('Curriculum'),
        required=False,
    )
    # Foreign higher education
    study_cycle_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + ForeignStudyCycleType.choices(),
        label=_("Study cycle type"),
        required=False,
    )
    linguistic_regime = forms.CharField(
        label=_("Linguistic regime"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
        required=False,
        empty_value=None,
    )
    transcript_translation = FileUploadField(
        label=_('Transcript translation'),
        required=False,
    )
    graduate_degree_translation = FileUploadField(
        label=_('Graduate degree translation'),
        required=False,
    )
    # Other occupation
    activity_type = forms.ChoiceField(
        choices=ActivityType.choices(),
        label=_('Activity type'),
        required=True,
        widget=forms.RadioSelect,
    )
    other_activity_type = forms.CharField(
        label=_('Other activity type'),
        required=False,
    )
    activity_certificate = FileUploadField(
        label=_('Activity certificate'),
        required=False,
    )
    activity_position = forms.CharField(
        label=_('Activity position'),
        required=False,
    )
    activity_institute_name = forms.CharField(
        label=_("Institute name"),
        required=False,
    )
    activity_institute_city = forms.CharField(
        label=_("Institute city"),
        required=False,
    )

    class Media:
        js = (
            'dependsOn.min.js',
            'jquery.mask.min.js',
        )

    def __init__(self, *args, person=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Init the form fields

        self.fields["academic_year"].choices = get_academic_year_initial_choices(person)

        # country = self.data.get(self.add_prefix("country"), self.initial.get("country"))
        # if country:
        #     self.fields['country'].choices = (country.iso_code, country.name,)

    def clean(self):
        # breakpoint()
        cleaned_data = super().clean()

        # List the fields that are mandatory depending on the values of other fields
        mandatory_fields = []

        if cleaned_data.get('type') == ExperienceType.HIGHER_EDUCATION.name:
            # Higher education
            is_belgian_education = cleaned_data.get('country') == BE_ISO_CODE

            mandatory_fields += [
                'acquired_credits_number',
                'credit_type',
                'dissertation_title',
                'dissertation_summary',
                'entered_credits_number',
                'result',
            ]

            if cleaned_data.get('dissertation_score') is None:
                self.add_error('dissertation_score', _('This field is required.'))

            # Institute
            if cleaned_data.get('institute_not_found'):
                mandatory_fields += [
                    'institute_city_be' if is_belgian_education else 'institute_city',
                    'institute_name',
                    'institute_postal_code',
                ]
            elif not cleaned_data.get('study_cycle_type') == ForeignStudyCycleType.OTHER_HIGHER_EDUCATION.name:
                mandatory_fields.append('institute')

            # Result
            if cleaned_data.get('result') in {Result.SUCCESS.name, Result.SUCCESS_WITH_RESIDUAL_CREDITS}:
                if cleaned_data.get('graduation_year'):
                    mandatory_fields.append('obtained_grade')

            if is_belgian_education:
                # Belgium studies
                mandatory_fields += [
                    'belgian_education_community',
                    'study_system',
                ]

                if cleaned_data.get('belgian_education_community') == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
                    if cleaned_data.get('program_not_found'):
                        mandatory_fields.append('other_program')
                        cleaned_data['program_name'] = cleaned_data['other_program']
                    else:
                        mandatory_fields.append('program')
                else:
                    mandatory_fields.append('education_name')

                cleaned_data['institute_city'] = cleaned_data['institute_city_be']

            else:
                # Foreign studies
                mandatory_fields += [
                    'study_cycle_type',
                    'linguistic_regime',
                    'education_name'
                ]
        else:
            # Other occupations
            mandatory_fields += [
                'activity_type',
                'activity_certificate',
            ]
            activity_type = cleaned_data.get('activity_type')
            if activity_type == ActivityType.OTHER.name:
                mandatory_fields.append('other_activity_type')
            if activity_type in {
                ActivityType.WORK.name,
                ActivityType.INTERNSHIP.name,
                ActivityType.VOLUNTEERING.name,
                ActivityType.OTHER.name,
            }:
                mandatory_fields.append('activity_institute_city')
            cleaned_data['institute_city'] = cleaned_data['activity_institute_city']
            cleaned_data['institute_name'] = cleaned_data['activity_institute_name']

        for field in mandatory_fields:
            if not cleaned_data.get(field):
                self.add_error(field, _('This field is required.'))

        return cleaned_data
