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
from django.views.generic import FormView

from admission.contrib.forms.cotutelle import DoctorateAdmissionCotutelleForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionCotutelleService, AdmissionPropositionService
from osis_document.api.utils import get_remote_token


class DoctorateAdmissionCotutelleFormView(WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_cotutelle.html'
    form_class = DoctorateAdmissionCotutelleForm

    def get_initial(self):
        cotutelle = AdmissionCotutelleService.get_cotutelle(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )
        initial = cotutelle.to_dict()
        if initial['cotutelle'] is not None:
            initial['cotutelle'] = 'YES' if initial['cotutelle'] else 'NO'
        document_fields = [
            'demande_ouverture',
            'convention',
            'autres_documents',
        ]
        for field in document_fields:
            initial[field] = [get_remote_token(document, write_token=True)
                              for document in initial.get(field)]
        return initial

    def call_webservice(self, data):
        AdmissionCotutelleService.update_cotutelle(person=self.person, **data)

    def prepare_data(self, data: dict):
        if data['cotutelle'] == 'NO':
            data.update(
                motivation="",
                institution="",
                demande_ouverture=[],
                convention=[],
                autres_documents=[],
            )
        del data['cotutelle']
        data['uuid'] = str(self.kwargs['pk'])
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admission'] = AdmissionPropositionService.get_proposition(
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )
        return context
