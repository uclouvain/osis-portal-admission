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
from datetime import datetime

from dal import autocomplete
from django import forms
from django.forms import BaseFormSet
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _, pgettext_lazy as __

from admission.constants import (
    BE_ISO_CODE,
    FIELD_REQUIRED_MESSAGE,
    LINGUISTIC_REGIMES_WITHOUT_TRANSLATION,
    MINIMUM_YEAR,
)

from admission.contrib.enums.curriculum import *
from admission.contrib.forms import (
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_past_academic_years_choices,
    CustomDateInput,
    get_language_initial_choices,
    get_diploma_initial_choices,
    get_example_text,
    RadioBooleanField,
    get_superior_non_university_initial_choices,
    FORM_SET_PREFIX,
)
from osis_document.contrib.forms import FileUploadField

from admission.services.reference import CountriesService


class DoctorateAdmissionCurriculumFileForm(forms.Form):
    curriculum = FileUploadField(
        label=_('Curriculum vitae detailed, dated and signed'),
        required=True,
    )


def year_choices():
    return [EMPTY_CHOICE[0]] + [(year, year) for year in range(datetime.today().year, MINIMUM_YEAR, -1)]


def month_choices():
    return [EMPTY_CHOICE[0]] + [(index, month) for index, month in MONTHS.items()]


class DoctorateAdmissionCurriculumProfessionalExperienceForm(forms.Form):
    start_date_month = forms.ChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
    )
    end_date_month = forms.ChoiceField(
        choices=month_choices,
        label=_('Month'),
        widget=autocomplete.Select2(),
    )
    start_date_year = forms.ChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
    )
    end_date_year = forms.ChoiceField(
        choices=year_choices,
        label=_('Year'),
        widget=autocomplete.Select2(),
    )
    type = forms.ChoiceField(
        choices=EMPTY_CHOICE + ActivityType.choices(),
        label=_('Type'),
    )
    role = forms.CharField(
        label=__('curriculum', 'Role'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('e.g.: Librarian'),
            },
        ),
    )
    sector = forms.ChoiceField(
        choices=EMPTY_CHOICE + ActivitySector.choices(),
        label=_('Sector'),
        required=False,
    )
    institute_name = forms.CharField(
        label=_('Institute name'),
        required=False,
    )
    certificate = FileUploadField(
        label=_('Certificate'),
        required=False,
    )
    activity = forms.CharField(
        label=_('Activity'),
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get('start_date_month')
            and cleaned_data.get('end_date_month')
            and cleaned_data.get('start_date_year')
            and cleaned_data.get('start_date_month')
        ):
            start_date_month = int(cleaned_data.get('start_date_month'))
            end_date_month = int(cleaned_data.get('end_date_month'))
            start_date_year = int(cleaned_data.get('start_date_year'))
            end_date_year = int(cleaned_data.get('end_date_year'))

            if start_date_year > end_date_year or (
                start_date_year == end_date_year and start_date_month > end_date_month
            ):
                self.add_error(None, _("The start date must be equals or lower than the end date."))

        activity_type = cleaned_data.get('type')

        if activity_type == ActivityType.WORK.name:
            if not cleaned_data.get('role'):
                self.add_error('role', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['role'] = ''

        if activity_type in [ActivityType.WORK.name, ActivityType.INTERNSHIP.name, ActivityType.VOLUNTEERING.name]:
            if not cleaned_data.get('sector'):
                self.add_error('sector', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('institute_name'):
                self.add_error('institute_name', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['sector'] = ''
            cleaned_data['institute_name'] = ''

        if activity_type == ActivityType.OTHER.name:
            cleaned_data['certificate'] = []
            if not cleaned_data['activity']:
                self.add_error('activity', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['activity'] = ''

        return cleaned_data


class DoctorateAdmissionCurriculumEducationalExperienceForm(forms.Form):
    start = forms.ChoiceField(
        label=_('Start'),
        widget=autocomplete.Select2(),
    )
    end = forms.ChoiceField(
        label=_('End'),
        widget=autocomplete.Select2(),
    )
    country = forms.CharField(
        label=_('Country'),
        widget=autocomplete.ListSelect2(url='admission:autocomplete:country'),
    )
    other_institute = forms.BooleanField(
        label=_('Other institute'),
        required=False,
    )
    institute_name = forms.CharField(
        label=_('Institute name'),
        required=False,
    )
    institute_address = forms.CharField(
        label=_('Institute address'),
        required=False,
    )
    institute = forms.CharField(
        empty_value=None,
        label=_('Institute'),
        required=False,
        widget=autocomplete.ListSelect2(url='admission:autocomplete:superior-non-university'),
    )
    program = forms.CharField(
        empty_value=None,
        label=_('Program'),
        required=False,
        widget=autocomplete.ListSelect2(url='admission:autocomplete:diploma'),
    )
    other_program = forms.BooleanField(
        label=_('Other program'),
        required=False,
    )
    education_name = forms.CharField(
        label=_('Education name'),
        required=False,
    )
    evaluation_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + EvaluationSystem.choices(),
        label=_('Evaluation type'),
    )
    linguistic_regime = forms.CharField(
        empty_value=None,
        label=_('Linguistic regime'),
        required=False,
        widget=autocomplete.ListSelect2(url='admission:autocomplete:language'),
    )
    transcript_type = forms.ChoiceField(
        choices=EMPTY_CHOICE + TranscriptType.choices(),
        label=_('Transcript type'),
    )
    obtained_diploma = RadioBooleanField(
        label=_('Did you obtain a diploma at the end of this training?'),
    )
    obtained_grade = forms.ChoiceField(
        choices=EMPTY_CHOICE + Grade.choices(),
        label=_('Obtained grade'),
        required=False,
    )
    graduate_degree = FileUploadField(
        label=_('Graduate degree'),
        required=False,
    )
    graduate_degree_translation = FileUploadField(
        label=_('Graduate degree translation'),
        required=False,
    )
    transcript = FileUploadField(
        label=_('Transcript'),
        required=False,
    )
    transcript_translation = FileUploadField(
        label=_('Transcript translation'),
        required=False,
    )
    rank_in_diploma = forms.CharField(
        label=_('Rank in diploma'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': _('e.g.: 5th out of 30'),
            },
        ),
    )
    expected_graduation_date = forms.DateField(
        help_text=_('Date on which you expect to graduate.'),
        label=_('Expected graduation date'),
        required=False,
        widget=CustomDateInput(),
    )
    dissertation_title = forms.CharField(
        label=_('Title of the dissertation'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
            },
        ),
    )
    dissertation_score = forms.CharField(
        label=_('Dissertation score'),
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': get_example_text('15/20'),
            },
        ),
    )
    dissertation_summary = FileUploadField(
        label=_('Dissertation summary'),
        required=False,
    )
    bachelor_cycle_continuation = RadioBooleanField(
        label=_(
            'Do you want, on the basis of this training, to realize a cycle '
            'continuation for the bachelor you are registering for?'
        ),
        required=False,
    )
    diploma_equivalence = FileUploadField(
        label=_('Diploma equivalence'),
        required=False,
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
        )

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize the field with dynamic choices
        academic_years_choices = get_past_academic_years_choices(person)
        self.fields['start'].choices = academic_years_choices
        self.fields['end'].choices = academic_years_choices

        iso_code = self.data.get(self.add_prefix("country"), self.initial.get("country"))
        country = CountriesService.get_country(iso_code=iso_code, person=person) if iso_code else None

        self.fields['country'].is_ue_country = bool(country and country.european_union)
        self.fields['country'].widget.choices = get_country_initial_choices(
            iso_code=iso_code,
            person=person,
            loaded_country=country,
        )

        self.fields['linguistic_regime'].widget.choices = get_language_initial_choices(
            self.data.get(self.add_prefix('linguistic_regime'), self.initial.get('linguistic_regime')),
            person,
        )

        self.fields['program'].widget.choices = get_diploma_initial_choices(
            self.data.get(self.add_prefix('program'), self.initial.get('program')),
            person,
        )

        self.fields['institute'].widget.choices = get_superior_non_university_initial_choices(
            self.data.get(self.add_prefix('institute'), self.initial.get('institute')),
            person,
        )

        # Initialize the fields which are not automatically mapping
        if self.initial:
            self.initial['other_program'] = bool(self.initial.get('education_name'))
            self.initial['other_institute'] = bool(self.initial.get('institute_name'))

    def clean(self):
        cleaned_data = super().clean()

        country = cleaned_data.get('country')
        be_country = country == BE_ISO_CODE

        obtained_diploma = cleaned_data.get('obtained_diploma')

        global_transcript = cleaned_data.get('transcript_type') == TranscriptType.ONE_FOR_ALL_YEARS.name

        # Date fields
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        if start and end and int(start) > int(end):
            self.add_error(None, _("The start date must be equals or lower than the end date."))

        # Institute fields
        self.clean_data_institute(cleaned_data)

        # Transcript field
        if global_transcript:
            if not cleaned_data.get('transcript'):
                self.add_error('transcript', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['transcript'] = []
            cleaned_data['transcript_translation'] = []

        self.clean_data_diploma(cleaned_data, obtained_diploma)

        if be_country:
            self.clean_data_be(cleaned_data)
        elif country:
            self.clean_data_foreign(cleaned_data, global_transcript, obtained_diploma)

        return cleaned_data

    def clean_data_diploma(self, cleaned_data, obtained_diploma):
        if obtained_diploma:
            for field in [
                'obtained_grade',
                'expected_graduation_date',
                'dissertation_title',
                'dissertation_score',
                'dissertation_summary',
                'graduate_degree',
            ]:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['expected_graduation_date'] = None
            cleaned_data['dissertation_title'] = ''
            cleaned_data['dissertation_score'] = ''
            cleaned_data['dissertation_summary'] = []
            cleaned_data['graduate_degree'] = []
            cleaned_data['graduate_degree_translation'] = []
            cleaned_data['rank_in_diploma'] = ''

    def clean_data_institute(self, cleaned_data):
        institute = cleaned_data.get('institute')
        other_institute = cleaned_data.get('other_institute')
        if other_institute:
            if not cleaned_data.get('institute_name'):
                self.add_error('institute_name', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('institute_address'):
                self.add_error('institute_address', FIELD_REQUIRED_MESSAGE)

            cleaned_data['institute'] = None

        else:
            if not institute:
                self.add_error('institute', FIELD_REQUIRED_MESSAGE)

            cleaned_data['institute_address'] = ''
            cleaned_data['institute_name'] = ''

    def clean_data_foreign(self, cleaned_data, global_transcript, obtained_diploma):
        # Program field
        if not cleaned_data.get('education_name'):
            self.add_error('education_name', FIELD_REQUIRED_MESSAGE)
        # Equivalence field
        if not cleaned_data.get('diploma_equivalence'):
            self.add_error('diploma_equivalence', FIELD_REQUIRED_MESSAGE)
        # Linguistic fields
        linguistic_regime = cleaned_data.get('linguistic_regime')
        if not linguistic_regime:
            self.add_error('linguistic_regime', FIELD_REQUIRED_MESSAGE)
        if not linguistic_regime or linguistic_regime in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION:
            cleaned_data['graduate_degree_translation'] = []
            cleaned_data['transcript_translation'] = []
        else:
            if obtained_diploma and not cleaned_data.get('graduate_degree_translation'):
                self.add_error('graduate_degree_translation', FIELD_REQUIRED_MESSAGE)
            if global_transcript and not cleaned_data.get('transcript_translation'):
                self.add_error('transcript_translation', FIELD_REQUIRED_MESSAGE)
        # Clean belgian fields
        cleaned_data['program'] = None

    def clean_data_be(self, cleaned_data):
        # Program fields
        if cleaned_data.get('other_program'):
            if not cleaned_data.get('education_name'):
                self.add_error('education_name', FIELD_REQUIRED_MESSAGE)
            cleaned_data['program'] = None
        else:
            if not cleaned_data.get('program'):
                self.add_error('program', FIELD_REQUIRED_MESSAGE)
            cleaned_data['education_name'] = ''
        # Clean foreign fields
        cleaned_data['linguistic_regime'] = None
        cleaned_data['graduate_degree_translation'] = []
        cleaned_data['transcript_translation'] = []
        cleaned_data['diploma_equivalence'] = []


MINIMUM_CREDIT_NUMBER = 0


class DoctorateAdmissionCurriculumEducationalExperienceYearForm(forms.Form):

    def __init__(self, prefix_index_start=0, **kwargs):
        super().__init__(**kwargs)

    academic_year = forms.IntegerField(
        initial=FORM_SET_PREFIX,
        label=_('Academic year'),
        widget=forms.HiddenInput(),
    )
    is_enrolled = forms.BooleanField(
        initial=True,
        label=_('Enrolled'),
        required=False,
    )
    result = forms.ChoiceField(
        choices=EMPTY_CHOICE + Result.choices(),
        label=_('Result'),
        required=False,
    )
    registered_credit_number = forms.FloatField(
        label=_('Registered credits'),
        required=False,
    )
    acquired_credit_number = forms.FloatField(
        label=_('Acquired credits'),
        required=False,
    )
    transcript = FileUploadField(
        label=_('Transcript'),
        max_files=1,
        required=False,
    )
    transcript_translation = FileUploadField(
        label=_('Transcript translation'),
        max_files=1,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('is_enrolled') and not cleaned_data.get('result'):
            self.add_error('result', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class BaseFormSetWithCustomFormIndex(BaseFormSet):
    def add_prefix(self, index):
        return super().add_prefix(
            self.form_kwargs.get('prefix_index_start') - index if isinstance(index, int) else index
        )


DoctorateAdmissionCurriculumEducationalExperienceYearFormSet = forms.formset_factory(
    form=DoctorateAdmissionCurriculumEducationalExperienceYearForm,
    formset=BaseFormSetWithCustomFormIndex,
    extra=0,
)
