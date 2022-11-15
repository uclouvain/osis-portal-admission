# #
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
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.contrib.enums.accounting import LienParente, FORMATTED_RELATIONSHIPS
from admission.contrib.forms.accounting import DoctorateAdmissionAccountingForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import (
    AdmissionPropositionService,
)


class DoctorateAdmissionAccountingFormView(
    LoadDossierViewMixin,
    WebServiceFormMixin,
    FormView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/forms/accounting.html'
    form_class = DoctorateAdmissionAccountingForm

    @cached_property
    def accounting_conditions(self):
        retrieved_accounting_conditions = AdmissionPropositionService.retrieve_accounting_conditions(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).to_dict()

        retrieved_accounting_conditions['education_site'] = self.admission.doctorat.campus

        return retrieved_accounting_conditions

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.accounting_conditions)
        context_data['relationships'] = {elt.name: elt.value for elt in LienParente}
        context_data['formatted_relationships'] = FORMATTED_RELATIONSHIPS
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.accounting_conditions)
        return kwargs

    def get_initial(self):
        return self.admission.comptabilite.to_dict() if self.admission.comptabilite else {}

    def call_webservice(self, data):
        AdmissionPropositionService.update_accounting(
            person=self.person,
            uuid=self.admission_uuid,
            data=data,
        )
