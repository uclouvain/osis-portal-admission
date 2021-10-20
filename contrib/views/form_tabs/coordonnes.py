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

from admission.contrib.forms.coordonnees import DoctorateAdmissionAddressForm, DoctorateAdmissionCoordonneesForm
from admission.services.mixins import WebServiceFormMixin

from admission.services.person import AdmissionPersonService
from admission.services.reference import CountriesService


class DoctorateAdmissionCoordonneesFormView(WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_coordonnees.html'
    success_url = reverse_lazy('admission:doctorate-list')
    form_class = DoctorateAdmissionCoordonneesForm
    forms = None
    BE_ISO_CODE = None

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms())
        context_data["BE_ISO_CODE"] = self.BE_ISO_CODE
        return context_data

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms.values()):
            return self.form_valid(forms['main_form'])
        return self.form_invalid(forms['main_form'])

    def get_initial(self):
        return AdmissionPersonService.retrieve_person_coordonnees()

    @staticmethod
    def prepare_be_city(form_cleaned_data):
        """Check if a belgian postal code / city has been passed and update the form."""
        if form_cleaned_data['be_postal_code']:
            form_cleaned_data['postal_code'] = form_cleaned_data['be_postal_code']
            form_cleaned_data['city'] = form_cleaned_data['be_city']
            del form_cleaned_data['be_postal_code']
            del form_cleaned_data['be_city']

    def prepare_data(self, main_form_data):
        # Process the form data to match API
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()
        data = forms['main_form'].cleaned_data
        data['residential'] = forms['residential'].cleaned_data
        self.prepare_be_city(data['residential'])
        data['contact'] = forms['contact'].cleaned_data
        self.prepare_be_city(data['contact'])
        del data['show_contact']
        del data['email']
        return data

    def call_webservice(self, data):
        AdmissionPersonService.update_person_coordonnees(**data)

    def get_forms(self):
        if not self.forms:
            self.BE_ISO_CODE = CountriesService.get_country(name="Belgique")
            kwargs = self.get_form_kwargs()
            del kwargs['prefix']
            initial = kwargs['initial']
            del kwargs['initial']
            self.forms = {
                'main_form': self.get_form(),
                'contact': DoctorateAdmissionAddressForm(
                    prefix='contact',
                    initial=initial['contact'],
                    be_iso_code=self.BE_ISO_CODE,
                    **kwargs,
                ),
                'residential': DoctorateAdmissionAddressForm(
                    prefix='residential',
                    initial=initial['residential'],
                    be_iso_code=self.BE_ISO_CODE,
                    **kwargs,
                ),
            }
        return self.forms
