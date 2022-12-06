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

from admission.contrib.enums.specific_question import Onglets
from admission.contrib.views.mixins import LoadDossierViewMixin

__all__ = ['SpecificQuestionDetailView']

from admission.services.proposition import AdmissionPropositionService


class SpecificQuestionDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/details/specific_question.html'
    tab_of_specific_questions = Onglets.INFORMATIONS_ADDITIONNELLES.name

    @cached_property
    def pool_questions(self):
        return AdmissionPropositionService.get_pool_questions(self.person, self.admission_uuid).to_dict()

    def get_context_data(self, **kwargs):
        if self.current_context == 'general-education':
            kwargs['pool_questions'] = self.pool_questions
        return super().get_context_data(**kwargs)
