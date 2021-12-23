# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService


class DoctorateAdmissionRequestSignaturesView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/request_signatures.html"
    form_class = Form

    def call_webservice(self, data):
        AdmissionPropositionService.request_signatures(person=self.person, uuid=str(self.kwargs.get('pk')))

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        service_kwargs = {
            "person": self.person,
            "uuid": str(self.kwargs['pk']),
        }
        context_data["admission"] = AdmissionPropositionService.get_proposition(**service_kwargs)
        context_data["errors"] = AdmissionPropositionService.verify_proposition(**service_kwargs)
        return context_data

    def get_success_url(self):
        return resolve_url("admission:doctorate-list")
