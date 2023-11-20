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

from admission.contrib.enums import CHOIX_AFFILIATION_SPORT_SELON_SITE
from admission.contrib.enums.accounting import FORMATTED_RELATIONSHIPS
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['AdmissionAccountingDetailView']


class BaseAdmissionAccountingView(LoadDossierViewMixin):
    retrieve_accounting = {
        'doctorate': AdmissionPropositionService.retrieve_doctorate_accounting,
        'general-education': AdmissionPropositionService.retrieve_general_accounting,
    }

    @cached_property
    def accounting(self):
        return self.retrieve_accounting[self.current_context](
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).to_dict()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['accounting'] = self.accounting
        context_data['formatted_relationship'] = FORMATTED_RELATIONSHIPS.get(self.accounting['relation_parente'])
        context_data['with_assimilation'] = self.with_assimilation
        context_data['sport_affiliation_choices_by_campus'] = CHOIX_AFFILIATION_SPORT_SELON_SITE
        return context_data

    @property
    def with_assimilation(self):
        return self.accounting.get('a_nationalite_ue') is False


class AdmissionAccountingDetailView(BaseAdmissionAccountingView, TemplateView):
    template_name = 'admission/details/accounting.html'
