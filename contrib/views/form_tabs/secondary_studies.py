# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import reverse_lazy
from django.views.generic import FormView

from admission.contrib.enums.person import DiplomaTypes
from admission.contrib.forms.secondary_studies import (
    DoctorateAdmissionEducationForm,
    DoctorateAdmissionEducationForeignDiplomaForm,
    DoctorateAdmissionEducationBelgianDiplomaForm,
    DoctorateAdmissionEducationScheduleForm,
)
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService


class DoctorateAdmissionEducationFormView(WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/form_tab_education.html"
    success_url = reverse_lazy("admission:doctorate-list")
    form_class = DoctorateAdmissionEducationForm
    forms = None

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms())
        return context_data

    def get_initial(self):
        return AdmissionPersonService.retrieve_high_school_diploma(person=self.request.user.person)

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        if all(form.is_valid() for form in forms.values()):
            return self.form_valid(forms["main_form"])
        else:
            return self.form_invalid(forms["main_form"])

    def get_forms(self):
        if not self.forms:
            kwargs = self.get_form_kwargs()
            del kwargs["prefix"]
            initial = kwargs["initial"]
            del kwargs["initial"]
            self.forms = {
                "main_form": self.get_form(),
                "belgian_diploma_form": DoctorateAdmissionEducationBelgianDiplomaForm(
                    prefix="belgian_diploma",
                    initial=initial["belgian_diploma"],
                    empty_permitted=True,
                    use_required_attribute=False,
                    **kwargs,
                ),
                "foreign_diploma_form": DoctorateAdmissionEducationForeignDiplomaForm(
                    prefix="foreign_diploma",
                    initial=initial["foreign_diploma"],
                    empty_permitted=True,
                    use_required_attribute=False,
                    **kwargs,
                ),
                "schedule_form": DoctorateAdmissionEducationScheduleForm(
                    prefix="schedule",
                    initial=initial["belgian_diploma"]["schedule"] if initial["belgian_diploma"] else None,
                    empty_permitted=True,
                    use_required_attribute=False,
                    **kwargs,
                )
            }
        return self.forms

    def call_webservice(self, data):
        AdmissionPersonService.update_high_school_diploma(person=self.request.user.person, **data)

    @staticmethod
    def prepare_diploma(data, forms, diploma):
        data[diploma] = forms["{}_form".format(diploma)].cleaned_data
        data[diploma]["academic_graduation_year"] = data["academic_graduation_year"]
        data[diploma]["result"] = data["result"]
        del data["got_diploma"]
        del data["diploma_type"]
        del data["academic_graduation_year"]
        del data["result"]

    def prepare_data(self, main_form_data):
        # Process the form data to match API
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()

        data = forms["main_form"].cleaned_data

        if data.get("got_diploma"):
            if data.get("diploma_type") == DiplomaTypes.BELGIAN.name:
                self.prepare_diploma(data, forms, "belgian_diploma")
                if main_form_data.get("schedule"):
                    data["belgian_diploma"]["schedule"] = data["schedule"]
                    del data["schedule"]

            if data.get("diploma_type") == DiplomaTypes.FOREIGN.name:
                self.prepare_diploma(data, forms, "foreign_diploma")

        return data
