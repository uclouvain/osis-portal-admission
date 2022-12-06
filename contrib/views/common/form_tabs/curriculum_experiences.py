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
import calendar
import datetime
from abc import ABC
from decimal import Decimal

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.template import loader
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from admission.constants import (
    BE_ISO_CODE,
    FIELD_REQUIRED_MESSAGE,
    FIRST_YEAR_WITH_ECTS_BE,
    LINGUISTIC_REGIMES_WITHOUT_TRANSLATION,
)
from admission.contrib.enums import EvaluationSystem, EvaluationSystemsWithCredits, TranscriptType
from admission.contrib.forms import (
    FOLLOWING_FORM_SET_PREFIX,
    FORM_SET_PREFIX,
    OSIS_DOCUMENT_UPLOADER_CLASS,
    OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX,
)
from admission.contrib.forms.curriculum import (
    DoctorateAdmissionCurriculumEducationalExperienceForm,
    DoctorateAdmissionCurriculumEducationalExperienceYearFormSet,
    DoctorateAdmissionCurriculumProfessionalExperienceForm,
    MINIMUM_CREDIT_NUMBER,
)
from admission.contrib.views.common.detail_tabs.curriculum_experiences import (
    AdmissionCurriculumMixin,
    get_educational_experience_year_set_with_lost_years,
    initialize_field_texts,
)
from admission.services.mixins import WebServiceFormMixin

__all__ = [
    "AdmissionCurriculumFormMixin",
    "AdmissionCurriculumProfessionalExperienceFormView",
    "AdmissionCurriculumEducationalExperienceFormView",
    "AdmissionCurriculumProfessionalExperienceDeleteView",
    "AdmissionCurriculumEducationalExperienceDeleteView",
]
__namespace__ = 'curriculum'


class AdmissionCurriculumFormMixin(WebServiceFormMixin, AdmissionCurriculumMixin, ABC):
    def get_success_url(self):
        url = resolve_url(f"admission:{self.current_context}:update:curriculum", pk=self.admission_uuid)
        return url + getattr(self, 'url_hash', '')


class AdmissionCurriculumProfessionalExperienceFormView(AdmissionCurriculumFormMixin, FormView):
    urlpatterns = {
        'professional_update': 'professional/<uuid:experience_id>/update',
        'professional_create': 'professional/create',
    }
    template_name = 'admission/doctorate/forms/curriculum_professional_experience.html'
    form_class = DoctorateAdmissionCurriculumProfessionalExperienceForm
    url_hash = '#non-academic-activities'

    def prepare_data(self, data):
        # The start date is the first day of the specified month
        data['start_date'] = datetime.date(int(data.pop('start_date_year')), int(data.pop('start_date_month')), 1)
        # The end date is the last day of the specified month
        end_date_year = int(data.pop('end_date_year'))
        end_date_month = int(data.pop('end_date_month'))
        data['end_date'] = datetime.date(
            end_date_year, end_date_month, calendar.monthrange(end_date_year, end_date_month)[1]
        )
        return data

    def call_webservice(self, data):
        if self.experience_id:
            self.service_mapping[self.current_context].update_professional_experience(
                experience_id=self.experience_id,
                person=self.person,
                uuid=self.admission_uuid,
                data=data,
            )
        else:
            self.service_mapping[self.current_context].create_professional_experience(
                person=self.person,
                uuid=self.admission_uuid,
                data=data,
            )

    def get_initial(self):
        if self.experience_id:
            experience = self.professional_experience.to_dict()
            start_date = experience.pop('start_date')
            end_date = experience.pop('end_date')
            if start_date:
                experience['start_date_month'] = start_date.month
                experience['start_date_year'] = start_date.year
            if end_date:
                experience['end_date_month'] = end_date.month
                experience['end_date_year'] = end_date.year
            return experience


class AdmissionCurriculumProfessionalExperienceDeleteView(AdmissionCurriculumFormMixin, FormView):
    urlpatterns = {'professional_delete': 'professional/<uuid:experience_id>/delete'}
    form_class = forms.Form
    template_name = 'admission/doctorate/forms/curriculum_experience_delete.html'
    url_hash = '#non-academic-activities'

    def call_webservice(self, _):
        self.service_mapping[self.current_context].delete_professional_experience(
            experience_id=self.experience_id,
            person=self.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initialize_field_texts(self.person, [self.professional_experience])
        context['experience'] = self.professional_experience
        return context


class AdmissionCurriculumEducationalExperienceDeleteView(AdmissionCurriculumFormMixin, FormView):
    urlpatterns = {'educational_delete': 'educational/<uuid:experience_id>/delete'}
    extra_context = {
        'educational_tab': True,
    }
    form_class = forms.Form
    template_name = 'admission/doctorate/forms/curriculum_experience_delete.html'
    url_hash = '#academic-activities'

    def call_webservice(self, _):
        self.service_mapping[self.current_context].delete_educational_experience(
            experience_id=self.experience_id,
            person=self.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initialize_field_texts(self.person, [self.educational_experience])
        context['experience'] = self.educational_experience
        return context


class AdmissionCurriculumEducationalExperienceFormView(AdmissionCurriculumMixin, TemplateView):
    urlpatterns = {
        'educational_update': 'educational/<uuid:experience_id>/update',
        'educational_create': 'educational/create',
    }
    template_name = 'admission/doctorate/forms/curriculum_educational_experience.html'
    url_hash = '#academic-activities'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        educational_experience = None
        all_educational_experience_years = None

        if self.experience_id and self.request.method == 'GET':
            educational_experience = self.educational_experience.to_dict()
            all_years_config = get_educational_experience_year_set_with_lost_years(
                educational_experience.pop('educationalexperienceyear_set')
            )
            all_educational_experience_years = all_years_config['educational_experience_year_set_with_lost_years']
            educational_experience['start'] = all_years_config['start']
            educational_experience['end'] = all_years_config['end']

        base_form = DoctorateAdmissionCurriculumEducationalExperienceForm(
            person=self.request.user.person,
            data=self.request.POST or None,
            initial=educational_experience,
            prefix='base_form',
        )

        year_formset = DoctorateAdmissionCurriculumEducationalExperienceYearFormSet(
            self.request.POST or None,
            initial=all_educational_experience_years,
            prefix='year_formset',
            form_kwargs={
                'prefix_index_start': int(
                    base_form.data.get(
                        base_form.add_prefix('end'),
                        base_form.initial['end'] if all_educational_experience_years else 0,
                    )
                ),
            },
        )

        # We need to prevent the uploader component of osis-document from being initialized when the page is loaded
        # so that the events remain attached when the form is copied. The class identifying the component is replaced
        # in the default form and will be reset in the duplicated form, allowing osis-document to detect the file
        # fields in this new form, and set up the appropriate VueJS components.
        context_data["empty_form"] = loader.render_to_string(
            template_name='admission/doctorate/includes/curriculum_experience_year_form.html',
            context={
                'year_form': year_formset.empty_form,
                'next_year': FOLLOWING_FORM_SET_PREFIX,
            },
        ).replace(OSIS_DOCUMENT_UPLOADER_CLASS, OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX)

        context_data['base_form'] = base_form
        context_data['year_formset'] = year_formset
        context_data['linguistic_regimes_without_translation'] = LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
        context_data['BE_ISO_CODE'] = BE_ISO_CODE
        context_data['FIRST_YEAR_WITH_ECTS_BE'] = FIRST_YEAR_WITH_ECTS_BE
        context_data['FORM_SET_PREFIX'] = FORM_SET_PREFIX
        context_data['FOLLOWING_FORM_SET_PREFIX'] = FOLLOWING_FORM_SET_PREFIX
        context_data['OSIS_DOCUMENT_UPLOADER_CLASS'] = OSIS_DOCUMENT_UPLOADER_CLASS
        context_data['OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX'] = OSIS_DOCUMENT_UPLOADER_CLASS_PREFIX

        return context_data

    def prepare_data(self, base_form, year_formset):
        data = base_form.cleaned_data
        data['educationalexperienceyear_set'] = [
            year_data for year_data in year_formset.cleaned_data if year_data.pop('is_enrolled')
        ]

        data.pop('other_institute')
        data.pop('other_program')

        return data

    def check_forms(self, base_form, year_formset):
        # Individual form check
        base_form.is_valid()
        year_formset.is_valid()

        last_enrolled_year = None

        country = base_form.cleaned_data.get('country')
        be_country = country == BE_ISO_CODE
        linguistic_regime = base_form.cleaned_data.get('linguistic_regime')
        credits_are_required = base_form.cleaned_data.get('evaluation_type') in EvaluationSystemsWithCredits
        transcript_is_required = base_form.cleaned_data.get('transcript_type') == TranscriptType.ONE_A_YEAR.name
        transcript_translation_is_required = (
            transcript_is_required
            and country
            and not be_country
            and linguistic_regime
            and linguistic_regime not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
        )

        # Cross-form check
        for form in year_formset:
            if form.cleaned_data.get('is_enrolled'):
                if not last_enrolled_year:
                    last_enrolled_year = form.cleaned_data.get('academic_year')

                self.clean_experience_year_form(
                    be_country,
                    credits_are_required,
                    form,
                    transcript_is_required,
                    transcript_translation_is_required,
                )

        if not last_enrolled_year:
            base_form.add_error(None, _('At least one academic year is required.'))
        elif be_country:
            # The evaluation system in Belgium depends on the years
            base_form.cleaned_data['evaluation_type'] = EvaluationSystem[
                'ECTS_CREDITS' if last_enrolled_year >= FIRST_YEAR_WITH_ECTS_BE else 'NO_CREDIT_SYSTEM'
            ].name

        return base_form.is_valid() and year_formset.is_valid()

    def clean_experience_year_form(
        self,
        be_country,
        credits_are_required,
        form,
        transcript_is_required,
        transcript_translation_is_required,
    ):
        cleaned_data = form.cleaned_data

        # Credit fields
        if cleaned_data.get('academic_year') >= FIRST_YEAR_WITH_ECTS_BE if be_country else credits_are_required:

            acquired_credit_number = cleaned_data.get('acquired_credit_number', None)
            registered_credit_number = cleaned_data.get('registered_credit_number', None)

            if acquired_credit_number is None or acquired_credit_number == '':
                form.add_error('acquired_credit_number', FIELD_REQUIRED_MESSAGE)
            else:
                acquired_credit_number = Decimal(acquired_credit_number)
                if acquired_credit_number < MINIMUM_CREDIT_NUMBER:
                    form.add_error(
                        'acquired_credit_number',
                        _('This value must be equal to or greater than %(MINIMUM_CREDIT_NUMBER)s')
                        % {'MINIMUM_CREDIT_NUMBER': MINIMUM_CREDIT_NUMBER},
                    )

            if registered_credit_number is None or registered_credit_number == '':
                form.add_error('registered_credit_number', FIELD_REQUIRED_MESSAGE)
            else:
                registered_credit_number = Decimal(registered_credit_number)
                if registered_credit_number <= MINIMUM_CREDIT_NUMBER:
                    form.add_error(
                        'registered_credit_number',
                        _('This value must be greater than %(MINIMUM_CREDIT_NUMBER)s')
                        % {'MINIMUM_CREDIT_NUMBER': MINIMUM_CREDIT_NUMBER},
                    )

            if isinstance(acquired_credit_number, Decimal) and isinstance(registered_credit_number, Decimal):
                if acquired_credit_number > registered_credit_number:
                    form.add_error(
                        'acquired_credit_number',
                        _('This value cannot be greater than the entered credits number'),
                    )

        else:
            cleaned_data['acquired_credit_number'] = None
            cleaned_data['registered_credit_number'] = None

        # Transcript fields
        if transcript_is_required:
            if not cleaned_data.get('transcript'):
                form.add_error('transcript', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['transcript'] = []
        if transcript_translation_is_required:
            if not cleaned_data.get('transcript_translation'):
                form.add_error('transcript_translation', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['transcript_translation'] = []

    def post(self, request, *args, **kwargs):
        context_data = self.get_context_data(**kwargs)

        base_form = context_data['base_form']
        year_formset = context_data['year_formset']

        # Check the forms
        if not self.check_forms(base_form, year_formset):
            return self.render_to_response(context_data)

        # Prepare data
        data = self.prepare_data(base_form, year_formset)

        # Make the API request
        if self.experience_id:
            self.service_mapping[self.current_context].update_educational_experience(
                experience_id=self.experience_id,
                person=self.request.user.person,
                uuid=self.admission_uuid,
                data=data,
            )
        else:
            self.service_mapping[self.current_context].create_educational_experience(
                person=self.request.user.person,
                uuid=self.admission_uuid,
                data=data,
            )

        return HttpResponseRedirect(self.get_success_url())
