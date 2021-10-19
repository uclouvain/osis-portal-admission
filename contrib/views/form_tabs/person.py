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

from django.urls import reverse_lazy
from django.views.generic import FormView

from admission.contrib.forms.person import DoctorateAdmissionPersonForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from osis_document.api.utils import get_remote_token


class DoctorateAdmissionPersonFormView(WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_person.html'
    success_url = reverse_lazy('admission:doctorate-list')
    form_class = DoctorateAdmissionPersonForm

    def get_initial(self):
        person = AdmissionPersonService.retrieve_person()
        initial = person.to_dict()
        document_fields = [
            'id_card',
            'passport',
            'id_photo',
        ]
        for field in document_fields:
            initial[field] = [get_remote_token(document, write_token=True)
                              for document in person.get(field)]
        return initial

    def call_webservice(self, data):
        AdmissionPersonService.update_person(**data)
