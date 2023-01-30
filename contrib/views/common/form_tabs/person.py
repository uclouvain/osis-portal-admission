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

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.person import IdentificationType
from admission.contrib.forms.person import DoctorateAdmissionPersonForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)

__all__ = ['AdmissionPersonFormView']


class AdmissionPersonFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    template_name = 'admission/forms/person.html'
    form_class = DoctorateAdmissionPersonForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resides_in_belgium'] = self.resides_in_belgium
        context['BE_ISO_CODE'] = BE_ISO_CODE
        return context

    @cached_property
    def person_info(self):
        return (
            self.service_mapping[self.current_context]
            .retrieve_person(
                self.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

    @property
    def resides_in_belgium(self):
        return self.person_info.get('resides_in_belgium')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        return kwargs

    def get_initial(self):
        return self.person_info

    def prepare_data(self, data):
        is_belgian = data.get('country_of_citizenship') == BE_ISO_CODE

        if not data['already_registered']:
            data['last_registration_year'] = None
            data['last_registration_id'] = ''
        else:
            data['last_registration_year'] = (
                int(data['last_registration_year']) if data['last_registration_year'] else None
            )

        if data['unknown_birth_date']:
            data['birth_date'] = None
        else:
            data['birth_year'] = None

        if (self.resides_in_belgium and is_belgian) or data.get('has_national_number'):
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []

        elif data.get('identification_type') == IdentificationType.ID_CARD_NUMBER.name:
            data['national_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []

        elif data.get('identification_type') == IdentificationType.PASSPORT_NUMBER.name:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['id_card'] = []

        else:
            data['national_number'] = ''
            data['id_card_number'] = ''
            data['passport_number'] = ''
            data['passport'] = []
            data['id_card'] = []

        for field in ['already_registered', 'unknown_birth_date', 'identification_type', 'has_national_number']:
            data.pop(field, None)

        return data

    def call_webservice(self, data):
        updated_person = self.service_mapping[self.current_context].update_person(
            person=self.person,
            data=data,
            uuid=self.admission_uuid,
        )
        # Update local person to make sure future requests to API don't rollback person
        update_fields = []
        for field in ['first_name', 'last_name']:
            if getattr(self.person, field) != updated_person.get(field):
                update_fields.append(field)
                setattr(self.person, field, updated_person.get(field))
        self.person.save(update_fields=update_fields)
