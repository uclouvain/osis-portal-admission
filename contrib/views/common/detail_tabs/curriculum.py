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
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from admission.constants import BE_ISO_CODE

# Do not remove the following import as it is used by enum_display templatetag
from admission.contrib.enums.curriculum import *
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TrainingType, VETERINARY_BACHELOR_CODE
from admission.contrib.forms.curriculum import TRAINING_TYPES_WITH_EQUIVALENCE
from admission.contrib.views.common.detail_tabs.curriculum_experiences import initialize_field_texts
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)

__all__ = ['AdmissionCurriculumDetailView']


class AdmissionCurriculumDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/details/curriculum.html'
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    tab_of_specific_questions = Onglets.CURRICULUM.name

    @cached_property
    def curriculum(self):
        return self.service_mapping[self.current_context].get_curriculum(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_template_names(self):
        return [
            f"admission/{self.formatted_current_context}/details/curriculum.html",
            'admission/details/curriculum.html',
        ]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        curriculum = self.curriculum

        context_data['professional_experiences'] = curriculum.professional_experiences
        context_data['educational_experiences'] = curriculum.educational_experiences
        context_data['minimal_date'] = curriculum.minimal_date
        context_data['need_to_complete'] = curriculum.minimal_date <= curriculum.maximal_date
        context_data['missing_periods_messages'] = curriculum.incomplete_periods
        context_data['incomplete_experiences'] = curriculum.incomplete_experiences
        context_data['display_curriculum'] = self.display_curriculum
        context_data['display_equivalence'] = self.display_equivalence
        context_data['display_bachelor_continuation'] = self.display_bachelor_continuation
        context_data['display_bachelor_continuation_attestation'] = self.display_bachelor_continuation_attestation
        context_data['BE_ISO_CODE'] = BE_ISO_CODE

        initialize_field_texts(self.request.user.person, context_data['educational_experiences'], self.current_context)

        return context_data

    @cached_property
    def has_foreign_diploma(self):
        return any(experience.country != BE_ISO_CODE for experience in self.curriculum.educational_experiences)

    @cached_property
    def has_belgian_diploma(self):
        return any(experience.country == BE_ISO_CODE for experience in self.curriculum.educational_experiences)

    @cached_property
    def has_success_year(self):
        return any(
            year['result'].value == Result.SUCCESS.name
            for experience in self.curriculum.educational_experiences
            for year in experience.educationalexperienceyear_set
        )

    @cached_property
    def display_curriculum(self):
        if self.current_context == 'general-education':
            return self.admission.formation['type'] != TrainingType.BACHELOR.name
        return True

    @cached_property
    def display_equivalence(self):
        if self.current_context == 'general-education':
            return self.admission.formation['type'] in TRAINING_TYPES_WITH_EQUIVALENCE and self.has_foreign_diploma
        elif self.current_context == 'continuing-education':
            return (
                self.admission.formation['type'] == TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name
                and self.has_foreign_diploma
            )
        return False

    @cached_property
    def display_bachelor_continuation(self):
        if self.current_context == 'general-education':
            return self.admission.formation['type'] == TrainingType.BACHELOR.name and self.has_success_year
        return False

    @cached_property
    def display_bachelor_continuation_attestation(self):
        return self.display_bachelor_continuation and self.admission.formation['sigle'] == VETERINARY_BACHELOR_CODE
