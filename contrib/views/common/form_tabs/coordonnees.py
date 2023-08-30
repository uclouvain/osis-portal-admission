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

from django.views.generic import FormView

from admission.constants import BE_ISO_CODE
from admission.contrib.forms.coordonnees import DoctorateAdmissionAddressForm, DoctorateAdmissionCoordonneesForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import (
    AdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)

__all__ = ['AdmissionCoordonneesFormView']

from admission.services.proposition import PostalCodeBusinessException


class AdmissionCoordonneesFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/forms/coordonnees.html'
    form_class = DoctorateAdmissionCoordonneesForm
    forms = None
    service_mapping = {
        'create': AdmissionPersonService,
        'doctorate': AdmissionPersonService,
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    error_mapping_contact = {
        PostalCodeBusinessException.PersonContactAddressBadPostalCodeFormatException: "postal_code",
    }
    error_mapping_residential = {
        PostalCodeBusinessException.PersonResidentialAddressBadPostalCodeFormatException: "postal_code",
    }

    def __init__(self, *args, **kwargs):
        self._error_mapping_contact = {exc.value: field for exc, field in self.error_mapping_contact.items()}
        self._error_mapping_residential = {exc.value: field for exc, field in self.error_mapping_residential.items()}
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms())
        context_data["BE_ISO_CODE"] = BE_ISO_CODE
        return context_data

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms.values()):
            return self.form_valid(forms['main_form'])
        return self.form_invalid(forms['main_form'])

    def get_initial(self):
        return (
            self.service_mapping[self.current_context]
            .retrieve_person_coordonnees(
                self.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

    @staticmethod
    def prepare_be_city(form_cleaned_data):
        """Check if a belgian postal code / city has been passed and update the form."""
        if form_cleaned_data['country'] == BE_ISO_CODE:
            form_cleaned_data['postal_code'] = form_cleaned_data['be_postal_code']
            form_cleaned_data['city'] = form_cleaned_data['be_city']
        form_cleaned_data.pop('be_postal_code')
        form_cleaned_data.pop('be_city')

    def prepare_data(self, main_form_data):
        # Process the form data to match API
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()
        data = forms['main_form'].cleaned_data
        data['residential'] = forms['residential'].cleaned_data
        self.prepare_be_city(data['residential'])
        if data.pop('show_contact'):
            data['contact'] = forms['contact'].cleaned_data
            self.prepare_be_city(data['contact'])
        else:
            data['contact'] = None
        return data

    def call_webservice(self, data):
        self.service_mapping[self.current_context].update_person_coordonnees(
            person=self.person,
            uuid=self.admission_uuid,
            data=data,
        )

    def handle_form_exception(self, form, exception):
        if exception.status_code in self._error_mapping_contact:
            field = self._error_mapping_contact.get(exception.status_code)
            self.forms['contact'].add_error(field, exception.detail)
        elif exception.status_code in self._error_mapping_residential:
            field = self._error_mapping_residential.get(exception.status_code)
            self.forms['residential'].add_error(field, exception.detail)
        else:
            super().handle_form_exception(form, exception)

    def get_forms(self):
        if not self.forms:
            kwargs = self.get_form_kwargs()
            kwargs.pop('prefix')
            initial = kwargs.pop('initial')
            self.forms = {
                'main_form': self.get_form(),
                'contact': DoctorateAdmissionAddressForm(
                    person=self.person,
                    prefix='contact',
                    initial=initial['contact'],
                    check_coordinates_fields=bool(kwargs.get('data') and kwargs['data'].get('show_contact')),
                    **kwargs,
                ),
                'residential': DoctorateAdmissionAddressForm(
                    person=self.person,
                    prefix='residential',
                    initial=initial['residential'],
                    **kwargs,
                ),
            }
        return self.forms
