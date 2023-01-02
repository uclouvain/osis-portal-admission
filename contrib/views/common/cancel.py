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
from django.forms import Form
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService

__all__ = ['AdmissionCancelView']


class AdmissionCancelView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/forms/cancel.html"
    form_class = Form
    service_mapping = {
        'doctorate': AdmissionPropositionService.cancel_proposition,
        'general-education': AdmissionPropositionService.cancel_general_education_proposition,
        'continuing-education': AdmissionPropositionService.cancel_continuing_education_proposition,
    }

    def get_success_url(self):
        return resolve_url('admission:list')

    def call_webservice(self, data):
        self.service_mapping[self.current_context](person=self.person, uuid=self.admission_uuid)
