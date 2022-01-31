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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import FormView

from admission.contrib.enums.secondary_studies import DiplomaTypes, EducationalType, GotDiploma
from admission.contrib.forms.education import (
    DoctorateAdmissionEducationBelgianDiplomaForm,
    DoctorateAdmissionEducationForeignDiplomaForm,
    DoctorateAdmissionEducationForm,
    DoctorateAdmissionEducationScheduleForm,
    FIELD_REQUIRED_MESSAGE,
)
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from base.tests.factories.academic_year import get_current_year

LINGUISTIC_REGIMES_WITHOUT_TRANSLATION = ['FR', 'DE', 'EN', 'IT', 'PT', 'ES']

EDUCATIONAL_TYPES_REQUIRING_SCHEDULE = [
    EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
    EducationalType.TRANSITION_METHOD.name,
    EducationalType.ARTISTIC_TRANSITION.name,
]


class DoctorateAdmissionEducationFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/form_tab_education.html"
    success_url = reverse_lazy("admission:doctorate-list")
    form_class = DoctorateAdmissionEducationForm
    forms = None

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms())
        if 'pk' in self.kwargs:
            context_data['admission'] = AdmissionPropositionService.get_proposition(
                person=self.person, uuid=str(self.kwargs['pk']),
            )
        context_data['foreign_diploma_type_images'] = {
            'INTERNATIONAL_BACCALAUREATE': 'admission/images/IBO.png',
            'EUROPEAN_BACHELOR': 'admission/images/schola_europa.png',
        }
        context_data['linguistic_regimes_without_translation'] = LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
        context_data['educational_types_requiring_schedule'] = EDUCATIONAL_TYPES_REQUIRING_SCHEDULE
        return context_data

    def get_initial(self):
        return AdmissionPersonService.retrieve_high_school_diploma(
            person=self.person,
            uuid=self.kwargs.get('pk'),
        ).to_dict()

    @staticmethod
    def check_bound_and_set_required_attr(form):
        """Check if the passed form is bound. If it is, it means that we can set the use_required_attribute to False
        for form validation."""
        if form.is_bound:
            form.empty_permitted = False

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        self.check_bound_and_set_required_attr(forms["belgian_diploma_form"])
        foreign_diploma = forms["foreign_diploma_form"]
        self.check_bound_and_set_required_attr(foreign_diploma)

        # Cross-form check: make schedule required for some belgian diploma educational types
        if forms["belgian_diploma_form"].is_valid():
            educational_type_data = forms["belgian_diploma_form"].cleaned_data.get("educational_type")
            if educational_type_data in EDUCATIONAL_TYPES_REQUIRING_SCHEDULE:
                self.check_bound_and_set_required_attr(forms["schedule_form"])
            else:
                forms["schedule_form"].is_bound = False  # drop data if schedule is not required

        main_form = forms["main_form"]
        # Cross-form check: translated diploma required for some foreign diploma linguistic regime
        if (main_form.is_bound and foreign_diploma.is_bound
                and main_form.data.get(main_form.add_prefix("got_diploma")) == GotDiploma.YES.name
                and foreign_diploma.data.get(foreign_diploma.add_prefix("linguistic_regime"))
                not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
                and not foreign_diploma.fields['high_school_diploma_translation'].widget.value_from_datadict(
                    foreign_diploma.data,
                    foreign_diploma.files,
                    foreign_diploma.add_prefix("high_school_diploma_translation")
                )):
            foreign_diploma.add_error("high_school_diploma_translation", FIELD_REQUIRED_MESSAGE)

        # Page is valid if all bound forms are valid
        if all(not form.is_bound or form.is_valid() for form in forms.values()):
            return self.form_valid(main_form)
        return self.form_invalid(main_form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.person
        return kwargs

    def get_forms(self):
        if not self.forms:
            kwargs = self.get_form_kwargs()
            data = kwargs.pop("data", None)
            # We don't work with files on those forms
            kwargs.pop("files", None)
            person = kwargs.pop("person")
            kwargs.pop("prefix")
            initial = kwargs.pop("initial")
            self.forms = {
                "main_form": self.get_form(),
                "belgian_diploma_form": DoctorateAdmissionEducationBelgianDiplomaForm(
                    prefix="belgian_diploma",
                    initial=initial.get("belgian_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    # don't send data to prevent validation
                    data=data if data and data.get("diploma_type") == DiplomaTypes.BELGIAN.name else None,
                    **kwargs,
                ),
                "foreign_diploma_form": DoctorateAdmissionEducationForeignDiplomaForm(
                    prefix="foreign_diploma",
                    initial=initial.get("foreign_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    person=person,
                    data=data if data and data.get("diploma_type") == DiplomaTypes.FOREIGN.name else None,
                    **kwargs,
                ),
                "schedule_form": DoctorateAdmissionEducationScheduleForm(
                    prefix="schedule",
                    initial=initial.get("belgian_diploma") and initial["belgian_diploma"].get("schedule"),
                    data=data if data and data.get("diploma_type") == DiplomaTypes.BELGIAN.name else None,
                    empty_permitted=True,
                    use_required_attribute=False,  # for number input that can't be empty
                    **kwargs,
                )
            }
        return self.forms

    def call_webservice(self, data):
        AdmissionPersonService.update_high_school_diploma(
            self.person,
            data,
            uuid=self.kwargs.get('pk'),
        )

    @staticmethod
    def prepare_diploma(data, forms, diploma):
        data[diploma] = forms["{}_form".format(diploma)].cleaned_data
        data[diploma]["academic_graduation_year"] = data.pop("academic_graduation_year")
        data[diploma]["high_school_transcript"] = data.pop("high_school_transcript")
        if data[diploma]["academic_graduation_year"] == get_current_year():
            # Drop diploma info for current year
            data.pop("high_school_diploma")
            data[diploma]["high_school_diploma"] = []
            data[diploma].pop("high_school_diploma_translation", None)
            data[diploma]["high_school_diploma_translation"] = []
        else:
            # Include diploma info
            data[diploma]["high_school_diploma"] = data.pop("high_school_diploma")

    def prepare_data(self, main_form_data):
        # Process the form data to match API
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()

        data = forms["main_form"].cleaned_data

        got_diploma = data.pop("got_diploma")
        if got_diploma in [GotDiploma.NO.name, ""]:
            return {}

        if got_diploma == GotDiploma.THIS_YEAR.name:
            data["academic_graduation_year"] = get_current_year()

        if data.pop("diploma_type") == DiplomaTypes.BELGIAN.name:
            self.prepare_diploma(data, forms, "belgian_diploma")
            schedule = forms.get("schedule_form")
            educational_type = forms.get("belgian_diploma_form").cleaned_data.get("educational_type")
            if schedule and educational_type in EDUCATIONAL_TYPES_REQUIRING_SCHEDULE:
                data["belgian_diploma"]["schedule"] = schedule.cleaned_data

        else:
            self.prepare_diploma(data, forms, "foreign_diploma")

        return data
