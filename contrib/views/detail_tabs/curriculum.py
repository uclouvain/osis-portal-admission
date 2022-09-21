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
from django.conf import settings
from django.contrib import messages
from django.shortcuts import resolve_url
from django.utils.functional import cached_property
from django.utils.translation import get_language, gettext_lazy as _

# Do not remove the following import as it is used by enum_display templatetag
from osis_admission_sdk.model.professional_experience import ProfessionalExperience

from admission.contrib.enums.curriculum import *

from django.views.generic import TemplateView

from admission.contrib.views.mixins import LoadDossierViewMixin
from osis_admission_sdk.model.educational_experience import EducationalExperience

from admission.constants import BE_ISO_CODE
from admission.services.person import AdmissionPersonService
from admission.services.reference import CountriesService, LanguageService, DiplomaService, SuperiorNonUniversityService


class DoctorateAdmissionCurriculumDetailView(LoadDossierViewMixin, TemplateView):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/details/curriculum.html'

    @cached_property
    def curriculum(self):
        return AdmissionPersonService.get_curriculum(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        curriculum = self.curriculum

        context_data['professional_experiences'] = curriculum.professional_experiences
        context_data['educational_experiences'] = curriculum.educational_experiences
        context_data['curriculum_file'] = curriculum.file
        context_data['minimal_year'] = curriculum.minimal_year

        context_data['BE_ISO_CODE'] = BE_ISO_CODE

        initialize_field_texts(self.request.user.person, context_data['educational_experiences'])

        return context_data


class DoctorateAdmissionCurriculumMixin(LoadDossierViewMixin):
    @cached_property
    def experience_id(self) -> str:
        return str(self.kwargs.get('experience_id', ''))

    @cached_property
    def professional_experience(self) -> ProfessionalExperience:
        return AdmissionPersonService.retrieve_professional_experience(
            experience_id=self.experience_id,
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    @cached_property
    def educational_experience(self) -> EducationalExperience:
        return AdmissionPersonService.retrieve_educational_experience(
            experience_id=self.experience_id,
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_success_url(self):
        # Redirect to the list of experiences
        messages.info(self.request, _("Your data has been saved"))
        return (
            resolve_url('admission:doctorate:update:curriculum', pk=self.admission_uuid)
            if self.admission_uuid
            else resolve_url('admission:doctorate-create:curriculum')
        )


def get_educational_experience_year_set_with_lost_years(educational_experience_year_set):
    educational_experience_year_set_with_lost_years = []
    start = None
    end = None

    if educational_experience_year_set:
        start = educational_experience_year_set[-1]['academic_year']
        end = educational_experience_year_set[0]['academic_year']

        taken_years = {experience['academic_year']: experience for experience in educational_experience_year_set}

        educational_experience_year_set_with_lost_years = [
            taken_years.get(
                year,
                {
                    'academic_year': year,
                    'is_enrolled': False,
                },
            )
            for year in range(end, start - 1, -1)
        ]

    return {
        'start': start,
        'end': end,
        'educational_experience_year_set_with_lost_years': educational_experience_year_set_with_lost_years,
    }


class DoctorateAdmissionCurriculumProfessionalExperienceDetailView(
    DoctorateAdmissionCurriculumMixin,
    TemplateView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/details/curriculum_professional_experience.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experience'] = self.professional_experience
        return context


class DoctorateAdmissionCurriculumEducationalExperienceDetailView(
    DoctorateAdmissionCurriculumMixin,
    TemplateView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/details/curriculum_educational_experience.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experience'] = self.educational_experience

        all_years_config = get_educational_experience_year_set_with_lost_years(
            self.educational_experience.educationalexperienceyear_set
        )
        context['experience_years'] = all_years_config['educational_experience_year_set_with_lost_years']
        context['experience'].start = all_years_config['start']
        context['experience'].end = all_years_config['end']

        context['experience'].evaluation_system_with_credits = (
            self.educational_experience.evaluation_type.value in EvaluationSystemsWithCredits
        )
        initialize_field_texts(self.request.user.person, [self.educational_experience])
        return context


def initialize_field_texts(person, curriculum_experiences):
    """
    Add into each experience, the names of the country and the linguistic regime.
    """
    is_supported_language = get_language() == settings.LANGUAGE_CODE

    for experience in curriculum_experiences:

        # Initialize the country
        if getattr(experience, 'country', None):
            country = CountriesService.get_country(
                iso_code=experience.country,
                person=person,
            )
            experience.country_name = country.name if is_supported_language else country.name_en

        # Initialize the linguistic regime
        if getattr(experience, 'linguistic_regime', None):
            linguistic_regime = LanguageService.get_language(
                code=experience.linguistic_regime,
                person=person,
            )
            experience.linguistic_regime_name = (
                linguistic_regime.name if is_supported_language else linguistic_regime.name_en
            )

        # Initialize the program
        if getattr(experience, 'program', None):
            program = DiplomaService.get_diploma(
                uuid=experience.program,
                person=person,
            )
            experience.education_name = program.title

        # Initialize the institute
        if getattr(experience, 'institute', None):
            institute = SuperiorNonUniversityService.get_superior_non_university(
                uuid=experience.institute,
                person=person,
            )
            experience.institute_name = institute.name
