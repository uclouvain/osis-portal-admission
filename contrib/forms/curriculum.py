# ##############################################################################
#
#     OSIS stands for Open Student Information System. It's an application
#     designed to manage the core business of higher education institutions,
#     such as universities, faculties, institutes and professional schools.
#     The core business involves the administration of students, teachers,
#     courses, programs and so on.
#
#     Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from admission.contrib.forms import (
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_past_academic_years_choices,
    CustomDateInput,
    get_language_initial_choices,
)
from osis_document.contrib.forms import FileUploadField


class DoctorateAdmissionCurriculumFileForm(forms.Form):
    curriculum = FileUploadField(
        help_text=_('This document must be detailed, dated and signed.'),
        label=_('Curriculum'),
        required=True,
    )


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
    # Common university higher education
    institute = forms.CharField(
        label=_("Institute"),
        required=False,
        empty_value=None,
        # TODO Enable the field and add autocomplete
        disabled=True,
    )
    institute_not_found = forms.BooleanField(
        label=_("I don't find my institute in the list."),
        required=False,
    )
    institute_name = forms.CharField(
        label=_("Institute name"),
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
        widget=CustomDateInput(),
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
        label=_('Title of the dissertation'),
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
    institute_city_be = forms.CharField(
        label=_("Institute city"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:city",
            forward=(forward.Field('institute_postal_code', 'postal_code'),),
        ),
    )
    program = forms.CharField(
        label=_("Program"),
        required=False,
        empty_value=None,
        # TODO Enable the field and add autocomplete
        disabled=True,
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
    # Foreign higher education
    institute_city = forms.CharField(
        label=_("Institute city"),
        required=False,
    )
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
        required=False,
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
        js = ('dependsOn.min.js',)

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Init the form fields
        self.fields["academic_year"].choices = get_past_academic_years_choices(person)

        if self.initial:
            # with the api data
            # > initialize the choices of autocomplete fields
            # > initialize the fields which are not automatically mapping

            curriculum_year = self.initial.get('curriculum_year')
            if curriculum_year:
                self.initial["academic_year"] = curriculum_year.get('academic_year')

            initial_country = self.initial.get('country')
            if initial_country:
                self.fields['country'].widget.choices = ((initial_country['iso_code'], initial_country['name']),)
                self.initial['country'] = initial_country['iso_code']

            initial_linguistic_regime = self.initial.get('linguistic_regime')
            if initial_linguistic_regime:
                self.fields['linguistic_regime'].widget.choices = (
                    (initial_linguistic_regime.get('code'), initial_linguistic_regime['name']),
                )
                self.initial['linguistic_regime'] = initial_linguistic_regime['code']

            initial_education_name = self.initial.get('education_name')
            if initial_education_name:
                self.initial['other_program'] = initial_education_name
                self.initial['program_not_found'] = True

            if self.initial.get('institute_name'):
                self.initial['institute_not_found'] = True

            initial_institute_city = self.initial.get('institute_city')
            if initial_institute_city:
                if self.initial.get('country') == BE_ISO_CODE:
                    self.fields['institute_city_be'].widget.choices = (
                        (initial_institute_city, initial_institute_city),
                    )

                self.initial['institute_city_be'] = initial_institute_city
                self.initial['activity_institute_city'] = initial_institute_city

            self.initial['activity_institute_name'] = self.initial.get('institute_name')

        else:
            # with the POST request data
            # > initialize the choices of autocomplete fields

            self.fields['country'].widget.choices = get_country_initial_choices(
                self.data.get(self.add_prefix("country")),
                person,
            )

            self.fields['linguistic_regime'].widget.choices = get_language_initial_choices(
                self.data.get(self.add_prefix("linguistic_regime")),
                person,
            )

    def clean(self):
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

            # Either a known or an unknown institute
            if cleaned_data.get('institute_not_found'):
                mandatory_fields += [
                    'institute_city_be' if is_belgian_education else 'institute_city',
                    'institute_name',
                    'institute_postal_code',
                ]
            elif not cleaned_data.get('study_cycle_type') == ForeignStudyCycleType.OTHER_HIGHER_EDUCATION.name:
                mandatory_fields.append('institute')

            # Result
            if cleaned_data.get('result') in {
                Result.SUCCESS.name,
                Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
            } and cleaned_data.get('graduation_year'):
                mandatory_fields.append('obtained_grade')

            if is_belgian_education:
                # Belgian studies
                mandatory_fields += [
                    'belgian_education_community',
                    'study_system',
                ]

                cleaned_data['institute_city'] = cleaned_data['institute_city_be']

                belgian_education_community = cleaned_data.get('belgian_education_community')
                if belgian_education_community:
                    if belgian_education_community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
                        # French-speaking community -> program (either known or unknown)
                        if cleaned_data.get('program_not_found'):
                            mandatory_fields.append('other_program')
                            cleaned_data['education_name'] = cleaned_data['other_program']
                        else:
                            mandatory_fields.append('program')
                    else:
                        # Other speaking communities -> education
                        mandatory_fields.append('education_name')

            else:
                # Foreign studies
                mandatory_fields += [
                    'study_cycle_type',
                    'linguistic_regime',
                    'education_name',
                ]

        elif cleaned_data.get('type') == ExperienceType.OTHER_ACTIVITY.name:
            # Other occupations
            mandatory_fields += [
                'activity_type',
                'activity_certificate',
            ]

            activity_type = cleaned_data.get('activity_type')

            # Custom activity type
            if activity_type == ActivityType.OTHER.name:
                mandatory_fields.append('other_activity_type')

            # Specify the location if necessary
            if activity_type in {
                ActivityType.WORK.name,
                ActivityType.INTERNSHIP.name,
                ActivityType.VOLUNTEERING.name,
                ActivityType.OTHER.name,
            }:
                mandatory_fields.append('activity_institute_city')

            cleaned_data['institute_city'] = cleaned_data['activity_institute_city']
            cleaned_data['institute_name'] = cleaned_data['activity_institute_name']

        # Check fields and eventually add errors
        for field in mandatory_fields:
            if not cleaned_data.get(field):
                self.add_error(field, _('This field is required.'))

        return cleaned_data
