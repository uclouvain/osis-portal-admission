# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.constants import PLUS_5_ISO_CODES, BE_ISO_CODE
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.views.mixins import LoadDossierViewMixin

__all__ = ['SpecificQuestionDetailView']

from admission.services.proposition import AdmissionPropositionService


class SpecificQuestionViewMixin(LoadDossierViewMixin):
    tab_of_specific_questions = Onglets.INFORMATIONS_ADDITIONNELLES.name

    @cached_property
    def pool_questions(self):
        return AdmissionPropositionService.get_pool_questions(self.person, self.admission_uuid).to_dict()

    @cached_property
    def identification(self):
        if self.is_general:
            return AdmissionPropositionService.retrieve_general_identification(
                person=self.person,
                uuid_proposition=self.admission_uuid,
            )

    @cached_property
    def display_visa_question(self):
        identification = self.identification
        return (
            identification is not None
            and identification.pays_nationalite
            and identification.pays_residence
            and identification.pays_nationalite_europeen is False
            and identification.pays_nationalite not in PLUS_5_ISO_CODES
            and identification.pays_residence != BE_ISO_CODE
        )


class SpecificQuestionDetailView(SpecificQuestionViewMixin, TemplateView):
    template_name = 'admission/details/specific_question.html'

    def get_context_data(self, **kwargs):
        if (
            self.current_context == 'general-education'
            and self.admission.formation['type'] == TrainingType.BACHELOR.name
        ):
            kwargs['pool_questions'] = self.pool_questions
        return super().get_context_data(**kwargs)
