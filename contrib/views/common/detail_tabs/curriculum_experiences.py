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
from django.conf import settings
from django.shortcuts import render
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import TemplateView
from osis_admission_sdk.model.educational_experience import EducationalExperience
from osis_admission_sdk.model.professional_experience import ProfessionalExperience

from admission.constants import BE_ISO_CODE, LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
from admission.contrib.enums import (
    ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT,
    CURRICULUM_ACTIVITY_LABEL,
    EvaluationSystemsWithCredits,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)
from admission.services.reference import (
    DiplomaService,
    LanguageService,
    SuperiorInstituteService,
    SuperiorNonUniversityService,
)
from admission.utils import format_address

__all__ = [
    'initialize_field_texts',
    'experience_can_be_updated',
    'get_educational_experience_year_set_with_lost_years',
    'AdmissionCurriculumMixin',
    'AdmissionCurriculumProfessionalExperienceDetailView',
    'AdmissionCurriculumEducationalExperienceDetailView',
]
__namespace__ = 'curriculum'


class AdmissionCurriculumMixin(LoadDossierViewMixin):
    service_mapping = {
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }

    @cached_property
    def experience_id(self) -> str:
        return str(self.kwargs.get('experience_id', ''))

    @cached_property
    def professional_experience(self) -> ProfessionalExperience:
        return self.service_mapping[self.current_context].retrieve_professional_experience(
            experience_id=self.experience_id,
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    @cached_property
    def educational_experience(self) -> EducationalExperience:
        return self.service_mapping[self.current_context].retrieve_educational_experience(
            experience_id=self.experience_id,
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )


class AdmissionCurriculumProfessionalExperienceDetailView(AdmissionCurriculumMixin, TemplateView):
    urlpatterns = {'professional_read': 'professional/<uuid:experience_id>/'}
    template_name = 'admission/details/curriculum_professional_experience.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experience'] = self.professional_experience
        context['CURRICULUM_ACTIVITY_LABEL'] = CURRICULUM_ACTIVITY_LABEL
        context['can_be_updated'] = professional_experience_can_be_updated(
            self.professional_experience,
            self.current_context,
        )
        return context


class AdmissionCurriculumEducationalExperienceDetailView(AdmissionCurriculumMixin, TemplateView):
    urlpatterns = {'educational_read': 'educational/<uuid:experience_id>/'}
    template_name = 'admission/details/curriculum_educational_experience.html'

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
            self.educational_experience.evaluation_type in EvaluationSystemsWithCredits
        )

        context['is_foreign_experience'] = self.educational_experience.country != BE_ISO_CODE
        context['is_belgian_experience'] = self.educational_experience.country == BE_ISO_CODE
        context['translation_required'] = (
            self.educational_experience.linguistic_regime
            and self.educational_experience.linguistic_regime not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
        )

        initialize_field_texts(self.request.user.person, [self.educational_experience], self.current_context)
        return context


def get_educational_experience_year_set_with_lost_years(educational_experience_year_set):
    educational_experience_year_set_with_lost_years = []
    taken_years = {}
    start = None
    end = None

    if educational_experience_year_set:
        start = educational_experience_year_set[-1]['academic_year']
        end = educational_experience_year_set[0]['academic_year']

        taken_years = {experience['academic_year']: experience for experience in educational_experience_year_set}

        for year in range(end, start - 1, -1):
            if year not in taken_years:
                taken_years[year] = {
                    'academic_year': year,
                    'is_enrolled': False,
                }

            educational_experience_year_set_with_lost_years.append(taken_years[year])

    return {
        'start': start,
        'end': end,
        'educational_experience_year_set_with_lost_years': educational_experience_year_set_with_lost_years,
        'educational_experience_year_set_with_lost_years_by_year': taken_years,
    }


def initialize_field_texts(person, curriculum_experiences, context):
    """
    Add into each experience, the names of the country and the linguistic regime.
    """
    is_supported_language = get_language() == settings.LANGUAGE_CODE

    for experience in curriculum_experiences:

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
            institute = SuperiorInstituteService.get_superior_institute(
                uuid=experience.institute,
                person=person,
            )
            experience.institute_name = institute.name
            experience.institute_address = format_address(
                street_number=institute.street_number,
                street=institute.street,
                postal_code=institute.zipcode,
                city=institute.city,
            )

        experience.can_be_updated = experience_can_be_updated(experience, context)


def experience_can_be_updated(experience, context):
    """Return if the educational experience can be updated in the specific context."""
    # An experience can be updated...
    return (
        # ... if it is not valuated
        not getattr(experience, 'valuated_from_trainings', [])
        # ... or, for a doctorate admission, if it hasn't been valuated by another doctorate admission
        or context == 'doctorate'
        and not any(
            training in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['doctorate']
            for training in experience.valuated_from_trainings
        )
        # ... or, for a general admission, if the experience has only been valuated by continuing admissions
        or context == 'general-education'
        and all(
            training in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['continuing-education']
            for training in experience.valuated_from_trainings
        )
    ) and not getattr(
        experience,
        'external_id',
        None,
    )  # ... and if the experience doesn't come from EPC


def professional_experience_can_be_updated(experience, context):
    """Return if the educational experience can be updated in the specific context."""
    is_certificate_missing = context in ['doctorate', 'general-education'] and not experience['certificate']
    # An experience can be updated...
    return (
        # ... if it is not valuated
        not getattr(experience, 'valuated_from_trainings', [])
        # ... or, for a doctorate / general admission,
        #     if it hasn't been valuated by another doctorate / general admission
        or (
            context in ['doctorate', 'general-education']
            and all(
                training in ADMISSION_EDUCATION_TYPE_BY_ADMISSION_CONTEXT['continuing-education']
                for training in experience.valuated_from_trainings
            )
        )
        # ... or, for a doctorate / general admission, certificate is missing
        or is_certificate_missing
    ) and (
        is_certificate_missing
        or not getattr(
            experience,
            'external_id',
            None,
        )  # ... and if the experience doesn't come from EPC or needs a certificate
    )
