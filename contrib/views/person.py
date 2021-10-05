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
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.views.generic import FormView, TemplateView

from admission.services.autocomplete import AdmissionAutocompleteService
from osis_document.api.utils import get_remote_token

from admission.contrib.forms.person import DoctorateAdmissionPersonForm
from admission.services.mixins import ApiExceptionErrorMappingMixin
from admission.services.person import AdmissionPersonService

__all__ = [
    "DoctorateAdmissionPersonFormView",
    "DoctorateAdmissionPersonDetailView",
]


class DoctorateAdmissionPersonDetailView(TemplateView):
    template_name = 'admission/doctorate/detail_person.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['person'] = AdmissionPersonService.retrieve_person()
        context_data['countries'] = {
            c.pk: (c.name if get_language() == settings.LANGUAGE_CODE else c.name_en)
            for c in AdmissionAutocompleteService().autocomplete_countries()
        }
        return context_data


class DoctorateAdmissionPersonFormView(ApiExceptionErrorMappingMixin, FormView):
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

    def prepare_data(self, data):
        # Process the form data to match API
        data['birth_country'] = int(data['birth_country']) if data['birth_country'] else None
        data['country_of_citizenship'] = (
            int(data['country_of_citizenship']) if data['country_of_citizenship'] else None
        )
        data['last_registration_year'] = (
            int(data['last_registration_year']) if data['last_registration_year'] else None
        )
        return data

    def call_webservice(self, data):
        AdmissionPersonService.update_person(**data)
