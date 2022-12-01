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

from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from admission.contrib.enums.accounting import FORMATTED_RELATIONSHIPS, dynamic_person_concerned_lowercase
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['AdmissionAccountingDetailView']


class AdmissionAccountingDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/accounting.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        retrieved_accounting_conditions = AdmissionPropositionService.retrieve_accounting_conditions(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).to_dict()

        context_data.update(retrieved_accounting_conditions)
        context_data['formatted_relationships'] = FORMATTED_RELATIONSHIPS
        context_data['dynamic_person_concerned_lowercase'] = mark_safe(dynamic_person_concerned_lowercase)

        return context_data

    def get_template_names(self):
        return [
            f'admission/{self.formatted_current_context}/details/accounting.html',
            'admission/details/wip.html',
        ]
