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
from django.views.generic import FormView

from admission.contrib.enums.accounting import FORMATTED_RELATIONSHIPS, LienParente
from admission.contrib.forms.accounting import AccountingForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['DoctorateAdmissionAccountingFormView']


class DoctorateAdmissionAccountingFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/forms/accounting.html'
    form_class = AccountingForm

    retrieve_accounting = {
        'doctorate': AdmissionPropositionService.retrieve_doctorate_accounting,
        'general-education': AdmissionPropositionService.retrieve_general_accounting,
        'continuing-education': AdmissionPropositionService.retrieve_continuing_accounting,
    }

    update_accounting = {
        'doctorate': AdmissionPropositionService.update_doctorate_accounting,
        'general-education': AdmissionPropositionService.update_general_accounting,
        'continuing-education': AdmissionPropositionService.update_continuing_accounting,
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
        context_data['relationships'] = {elt.name: elt.value for elt in LienParente}
        context_data['formatted_relationships'] = FORMATTED_RELATIONSHIPS
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_general_admission'] = self.current_context == 'general-education'
        if kwargs['is_general_admission']:
            kwargs['education_site'] = self.admission.formation.campus

        kwargs['has_ue_nationality'] = self.accounting.get('a_nationalite_ue')
        kwargs['last_french_community_high_education_institutes_attended'] = self.accounting.get(
            'derniers_etablissements_superieurs_communaute_fr_frequentes'
        )
        return kwargs

    def get_initial(self):
        return self.accounting

    def call_webservice(self, data):
        self.update_accounting[self.current_context](
            person=self.person,
            uuid=self.admission_uuid,
            data=data,
        )
