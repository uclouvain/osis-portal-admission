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
from django.views.generic import TemplateView

from admission.contrib.enums import TRAINING_TYPES_WITH_SCHOLARSHIP
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['TrainingChoiceDetailView']


class TrainingChoiceDetailView(LoadDossierViewMixin, TemplateView):
    tab_of_specific_questions = Onglets.CHOIX_FORMATION.name

    def get_context_data(self, **kwargs):
        # Check permission
        if self.current_context == 'general-education':
            AdmissionPropositionService.get_general_education_training_choice(
                self.request.user.person,
                uuid=self.admission_uuid,
            )
        elif self.current_context == 'continuing-education':
            AdmissionPropositionService.get_continuing_education_training_choice(
                self.request.user.person,
                uuid=self.admission_uuid,
            )

        context_data = super().get_context_data(**kwargs)
        context_data['TRAINING_TYPES_WITH_SCHOLARSHIP'] = TRAINING_TYPES_WITH_SCHOLARSHIP
        return context_data

    def get_template_names(self):
        return [
            f'admission/{self.formatted_current_context}/details/training_choice.html',
            'admission/details/training_choice.html',
        ]
