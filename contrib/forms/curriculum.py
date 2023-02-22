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
from copy import deepcopy
from datetime import datetime
from functools import partial
from typing import List

from dal import autocomplete
from django import forms
from django.forms import BaseFormSet
from django.utils.dates import MONTHS_ALT
from django.utils.translation import gettext_lazy as _, pgettext_lazy as __

from admission.contrib.enums import ADMISSION_CONTEXT_BY_ADMISSION_EDUCATION_TYPE
from osis_document.contrib.widgets import HiddenFileWidget

from admission.constants import (
    BE_ISO_CODE,
    FIELD_REQUIRED_MESSAGE,
    LINGUISTIC_REGIMES_WITHOUT_TRANSLATION,
    MINIMUM_YEAR,
)

from admission.contrib.enums.curriculum import *
from admission.contrib.enums.training_choice import TrainingType
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
    NoInput,
    AdmissionFileUploadField as FileUploadField,
)

from admission.contrib.forms.specific_question import ConfigurableFormMixin
from admission.services.reference import CountriesService


CurriculumField = partial(
    FileUploadField,
    label=_('Curriculum vitae detailed, dated and signed'),
    max_files=1,
    required=False,
)

DiplomaEquivalenceField = partial(
    FileUploadField,
    label=_(
        'Decision of equivalence for your diploma(s) giving access to the training, '
        'if this(these) has(have) been obtained outside Belgium'
    ),
    required=False,
)

TRAINING_TYPES_WITH_EQUIVALENCE = {
    TrainingType.AGGREGATION.name,
    TrainingType.CAPAES.name,
}

REQUIRED_FIELD_CLASS = 'required_field'


class DoctorateAdmissionCurriculumFileForm(ConfigurableFormMixin):
    configurable_form_field_name = 'reponses_questions_specifiques'

    curriculum = CurriculumField()


class GeneralAdmissionCurriculumFileForm(ConfigurableFormMixin):
    configurable_form_field_name = 'reponses_questions_specifiques'

    curriculum = CurriculumField()
    equivalence_diplome = DiplomaEquivalenceField()
    continuation_cycle_bachelier = RadioBooleanField(
        label=_(
            'Do you want, on the basis of this training, to realize a cycle '
            'continuation for the bachelor you are registering for?'
        ),
        required=False,
    )
    attestation_continuation_cycle_bachelier = FileUploadField(
        label=_("Certificate allowing the continuation of studies for a bachelor's degree in veterinary medicine"),
        required=False,
    )

    def __init__(
        self,
        display_equivalence: bool,
        display_curriculum: bool,
        display_bachelor_continuation: bool,
        display_bachelor_continuation_attestation: bool,
        has_belgian_diploma: bool,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not display_equivalence:
            self.fields['equivalence_diplome'].disabled = True
            self.fields['equivalence_diplome'].widget = NoInput()

        elif not has_belgian_diploma:
            self.fields['equivalence_diplome'].widget.attrs['class'] = REQUIRED_FIELD_CLASS

        if not display_curriculum:
            self.fields['curriculum'].disabled = True
            self.fields['curriculum'].widget = NoInput()

        if not display_bachelor_continuation:
            self.fields['continuation_cycle_bachelier'].disabled = True
            self.fields['continuation_cycle_bachelier'].widget = NoInput()

        if not display_bachelor_continuation_attestation:
            self.fields['attestation_continuation_cycle_bachelier'].disabled = True
            self.fields['attestation_continuation_cycle_bachelier'].widget = NoInput()

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data['continuation_cycle_bachelier']:
            cleaned_data['attestation_continuation_cycle_bachelier'] = []

        for f in ['curriculum', 'equivalence_diplome', 'attestation_continuation_cycle_bachelier']:
            if self.fields[f].disabled:
                cleaned_data[f] = []

        if self.fields['continuation_cycle_bachelier'].disabled:
            cleaned_data['continuation_cycle_bachelier'] = None

        return cleaned_data

    class Media:
        js = ('js/dependsOn.min.js',)


class ContinuingAdmissionCurriculumFileForm(ConfigurableFormMixin):
    configurable_form_field_name = 'reponses_questions_specifiques'

    curriculum = CurriculumField()
    equivalence_diplome = DiplomaEquivalenceField()

    def __init__(self, display_equivalence: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not display_equivalence:
            self.fields['equivalence_diplome'].disabled = True
            self.fields['equivalence_diplome'].widget = NoInput()

    def clean(self):
        cleaned_data = super().clean()

        if self.fields['equivalence_diplome'].disabled:
            cleaned_data['equivalence_diplome'] = []

        return cleaned_data


def year_choices():
    return [EMPTY_CHOICE[0]] + [(year, year) for year in range(datetime.today().year, MINIMUM_YEAR, -1)]


def month_choices():
    return [EMPTY_CHOICE[0]] + [(index, month) for index, month in MONTHS_ALT.items()]


class AdmissionCurriculumProfessionalExperienceForm(forms.Form):
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
        label=_('Employer'),
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

    def __init__(self, is_continuing, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_continuing = is_continuing
        if self.is_continuing:
            self.fields['certificate'].disabled = True
            self.fields['certificate'].widget = forms.MultipleHiddenInput()

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

        work_fields = ['role', 'sector', 'institute_name']

        if activity_type == ActivityType.WORK.name:
            for field in work_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            for field in work_fields:
                cleaned_data[field] = ''

        if activity_type == ActivityType.OTHER.name:
            cleaned_data['certificate'] = []
            if not cleaned_data['activity']:
                self.add_error('activity', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['activity'] = ''

        return cleaned_data


class ByContextAdmissionForm(forms.Form):
    """
    Hide and disable the fields that are not in the current context and disable the fields valuated by other contexts.
    """

    def __init__(self, educational_experience, current_context, fields_by_context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_by_context = fields_by_context
        self.current_context_fields = self.fields_by_context[current_context]

        self.disable_fields_other_contexts()

        if educational_experience and educational_experience.get('valuated_from_trainings'):
            self.disable_valuated_fields(educational_experience['valuated_from_trainings'])

    def disable_fields_other_contexts(self):
        """Disable and hide fields specific to other contexts."""
        for field in self.fields:
            if field not in self.current_context_fields:
                self.fields[field].disabled = True
                self.fields[field].widget = self.fields[field].hidden_widget()

    def disable_valuated_fields(self, valuated_education_types: List[str]):
        """Disable valuated fields"""
        valuated_contexts = set(
            ADMISSION_CONTEXT_BY_ADMISSION_EDUCATION_TYPE.get(training) for training in valuated_education_types
        )

        valuated_fields = set()
        for context in valuated_contexts:
            valuated_fields |= self.fields_by_context[context]

        for field in self.current_context_fields & valuated_fields:
            self.fields[field].disabled = True
            if isinstance(self.fields[field], FileUploadField):
                self.fields[field].widget = HiddenFileWidget(display_visualizer=True)

    def add_error(self, field, error):
        if field and self.fields[field].disabled:
            return
        super().add_error(field, error)


EDUCATIONAL_EXPERIENCE_BASE_FIELDS = {
    'start',
    'end',
    'country',
    'other_institute',
    'institute_name',
    'institute_address',
    'institute',
    'program',
    'other_program',
    'education_name',
    'obtained_diploma',
    'graduate_degree',
}

EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS = {
    'evaluation_type',
    'linguistic_regime',
    'transcript_type',
    'obtained_grade',
    'graduate_degree_translation',
    'transcript',
    'transcript_translation',
}

EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS = {
    'expected_graduation_date',
    'rank_in_diploma',
    'dissertation_title',
    'dissertation_score',
    'dissertation_summary',
}

EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT = {
    'doctorate': EDUCATIONAL_EXPERIENCE_BASE_FIELDS
    | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS
    | EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS,
    'general-education': EDUCATIONAL_EXPERIENCE_BASE_FIELDS | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS,
    'continuing-education': EDUCATIONAL_EXPERIENCE_BASE_FIELDS,
}


class AdmissionCurriculumEducationalExperienceForm(ByContextAdmissionForm):
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
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:superior-non-university',
            forward=['country'],
        ),
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
        label=_('Did you graduate from this training?'),
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
        label=_('Expected date of graduation (signed document)'),
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

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
        )

    def __init__(self, educational_experience, person, *args, **kwargs):
        kwargs.setdefault('initial', educational_experience)

        kwargs['fields_by_context'] = deepcopy(EDUCATIONAL_EXPERIENCE_FIELDS_BY_CONTEXT)

        if (
            educational_experience
            and educational_experience['valuated_from_trainings']
            and not educational_experience['graduate_degree']
        ):
            # If the experience has been valuated from a continuing admission and the graduate degree hasn't been set,
            # it is possible to set it once.
            kwargs['fields_by_context']['continuing-education'].remove('graduate_degree')

        super().__init__(educational_experience, *args, **kwargs)

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
        if not global_transcript:
            cleaned_data['transcript'] = []
            cleaned_data['transcript_translation'] = []

        self.clean_data_diploma(cleaned_data, obtained_diploma)

        if be_country:
            self.clean_data_be(cleaned_data)
        elif country:
            self.clean_data_foreign(cleaned_data)

        return cleaned_data

    def clean_data_diploma(self, cleaned_data, obtained_diploma):
        if obtained_diploma:
            for field in [
                'obtained_grade',
                'expected_graduation_date',
                'dissertation_title',
                'dissertation_score',
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

    def clean_data_foreign(self, cleaned_data):
        # Program field
        if not cleaned_data.get('education_name'):
            self.add_error('education_name', FIELD_REQUIRED_MESSAGE)
        # Linguistic fields
        linguistic_regime = cleaned_data.get('linguistic_regime')
        if not linguistic_regime:
            self.add_error('linguistic_regime', FIELD_REQUIRED_MESSAGE)
        if not linguistic_regime or linguistic_regime in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION:
            cleaned_data['graduate_degree_translation'] = []
            cleaned_data['transcript_translation'] = []
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


MINIMUM_CREDIT_NUMBER = 0


EDUCATIONAL_EXPERIENCE_YEAR_CONTINUING_FIELDS = {
    'academic_year',
}

EDUCATIONAL_EXPERIENCE_YEAR_FIELDS = {
    'academic_year',
    'is_enrolled',
    'result',
    'registered_credit_number',
    'acquired_credit_number',
    'transcript',
    'transcript_translation',
}

EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT = {
    'doctorate': EDUCATIONAL_EXPERIENCE_YEAR_FIELDS,
    'general-education': EDUCATIONAL_EXPERIENCE_YEAR_FIELDS,
    'continuing-education': EDUCATIONAL_EXPERIENCE_YEAR_CONTINUING_FIELDS,
}


class AdmissionCurriculumEducationalExperienceYearForm(ByContextAdmissionForm):
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
        localize=True,
    )
    acquired_credit_number = forms.FloatField(
        label=_('Acquired credits'),
        required=False,
        localize=True,
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

    def __init__(self, prefix_index_start=0, **kwargs):
        kwargs['fields_by_context'] = EDUCATIONAL_EXPERIENCE_YEAR_FIELDS_BY_CONTEXT
        super().__init__(**kwargs)

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


AdmissionCurriculumEducationalExperienceYearFormSet = forms.formset_factory(
    form=AdmissionCurriculumEducationalExperienceYearForm,
    formset=BaseFormSetWithCustomFormIndex,
    extra=0,
)
