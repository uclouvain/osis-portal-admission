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
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.constants import FIELD_REQUIRED_MESSAGE, LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
from admission.contrib.enums.secondary_studies import (
    DiplomaTypes,
    EducationalType,
    GotDiploma,
    ForeignDiplomaTypes,
    BelgianCommunitiesOfEducation,
    Equivalence,
    HAS_DIPLOMA_CHOICES,
)
from admission.contrib.forms.education import (
    DoctorateAdmissionEducationBelgianDiplomaForm,
    DoctorateAdmissionEducationForeignDiplomaForm,
    DoctorateAdmissionEducationForm,
    DoctorateAdmissionEducationScheduleForm,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from base.tests.factories.academic_year import get_current_year

EDUCATIONAL_TYPES_REQUIRING_SCHEDULE = [
    EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
]


class DoctorateAdmissionEducationFormView(
    LoadDossierViewMixin,
    WebServiceFormMixin,
    FormView,
):  # pylint: disable=too-many-ancestors
    template_name = "admission/doctorate/forms/education.html"
    success_url = reverse_lazy("admission:doctorate-list")
    form_class = DoctorateAdmissionEducationForm
    forms = None

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update(self.get_forms(context_data))
        context_data['foreign_diploma_type_images'] = {
            'INTERNATIONAL_BACCALAUREATE': 'admission/images/IBO.png',
            'EUROPEAN_BACHELOR': 'admission/images/schola_europa.png',
        }
        context_data['linguistic_regimes_without_translation'] = LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
        context_data['educational_types_requiring_schedule'] = EDUCATIONAL_TYPES_REQUIRING_SCHEDULE
        return context_data

    @cached_property
    def high_school_diploma(self):
        return AdmissionPersonService.retrieve_high_school_diploma(
            person=self.person,
            uuid=self.admission_uuid,
        ).to_dict()

    def get_initial(self):
        return self.high_school_diploma

    @staticmethod
    def check_bound_and_set_required_attr(form):
        """Check if the passed form is bound. If it is, it means that we can set the use_required_attribute to False
        for form validation."""
        if form.is_bound:
            form.empty_permitted = False

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()

        main_form = forms["main_form"]
        belgian_diploma_form = forms["belgian_diploma_form"]
        foreign_diploma_form = forms["foreign_diploma_form"]

        self.check_bound_and_set_required_attr(belgian_diploma_form)
        self.check_bound_and_set_required_attr(foreign_diploma_form)

        # Cross-form check: make schedule required for some belgian diploma educational types
        if belgian_diploma_form.is_bound:
            educational_type = belgian_diploma_form.data.get(belgian_diploma_form.add_prefix("educational_type"))
            community = belgian_diploma_form.data.get(belgian_diploma_form.add_prefix("community"))

            if (
                community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name
                and educational_type in EDUCATIONAL_TYPES_REQUIRING_SCHEDULE
            ):
                self.check_bound_and_set_required_attr(forms["schedule_form"])
            else:
                forms["schedule_form"].is_bound = False  # drop data if schedule is not required

        # Cross-form check for the foreign diploma
        if main_form.is_bound and foreign_diploma_form.is_bound:
            got_diploma = main_form.data.get(main_form.add_prefix("got_diploma"))
            high_school_diploma = main_form.fields['high_school_diploma'].widget.value_from_datadict(
                main_form.data, main_form.files, main_form.add_prefix("high_school_diploma")
            )
            enrolment_certificate = main_form.fields['enrolment_certificate'].widget.value_from_datadict(
                main_form.data, main_form.files, main_form.add_prefix("enrolment_certificate")
            )

            linguistic_regime = foreign_diploma_form.data.get(foreign_diploma_form.add_prefix("linguistic_regime"))

            high_school_diploma_translation = foreign_diploma_form.fields[
                'high_school_diploma_translation'
            ].widget.value_from_datadict(
                foreign_diploma_form.data,
                foreign_diploma_form.files,
                foreign_diploma_form.add_prefix("high_school_diploma_translation"),
            )
            enrolment_certificate_translation = foreign_diploma_form.fields[
                'enrolment_certificate_translation'
            ].widget.value_from_datadict(
                foreign_diploma_form.data,
                foreign_diploma_form.files,
                foreign_diploma_form.add_prefix("enrolment_certificate_translation"),
            )

            if got_diploma == GotDiploma.THIS_YEAR.name:
                if foreign_diploma_form.fields['country'].is_ue_country:
                    if not high_school_diploma and not enrolment_certificate:
                        main_form.add_error(
                            'high_school_diploma',
                            _('Please specify either your high school diploma or your enrolment certificate'),
                        )
                        main_form.add_error("enrolment_certificate", '')
                else:
                    if not high_school_diploma:
                        main_form.add_error("high_school_diploma", FIELD_REQUIRED_MESSAGE)

            # Translated files required for some foreign diploma linguistic regimes
            if linguistic_regime not in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION:
                self.clean_foreign_diploma_translation_fields(
                    foreign_diploma_form,
                    got_diploma,
                    enrolment_certificate,
                    enrolment_certificate_translation,
                    high_school_diploma,
                    high_school_diploma_translation,
                )

        # Page is valid if all bound forms are valid
        if all(not form.is_bound or form.is_valid() for form in forms.values()):
            return self.form_valid(main_form)
        return self.form_invalid(main_form)

    @classmethod
    def clean_foreign_diploma_translation_fields(
        cls,
        foreign_diploma_form,
        got_diploma,
        enrolment_certificate,
        enrolment_certificate_translation,
        high_school_diploma,
        high_school_diploma_translation,
    ):
        if got_diploma == GotDiploma.YES.name:
            # High school diploma is required
            if not high_school_diploma_translation:
                foreign_diploma_form.add_error("high_school_diploma_translation", FIELD_REQUIRED_MESSAGE)

        elif got_diploma == GotDiploma.THIS_YEAR.name:

            if foreign_diploma_form.fields['country'].is_ue_country:
                # Either high school diploma or enrolment certificate is required
                if high_school_diploma and not high_school_diploma_translation:
                    foreign_diploma_form.add_error("high_school_diploma_translation", FIELD_REQUIRED_MESSAGE)
                if enrolment_certificate and not enrolment_certificate_translation:
                    foreign_diploma_form.add_error("enrolment_certificate_translation", FIELD_REQUIRED_MESSAGE)
                if (
                    not high_school_diploma
                    and not enrolment_certificate
                    and not high_school_diploma_translation
                    and not enrolment_certificate_translation
                ):
                    # Empty errors because the related fields already have errors
                    foreign_diploma_form.add_error('high_school_diploma_translation', '')
                    foreign_diploma_form.add_error("enrolment_certificate_translation", '')

            elif not high_school_diploma_translation:
                # High school diploma is required
                foreign_diploma_form.add_error("high_school_diploma_translation", FIELD_REQUIRED_MESSAGE)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.person
        return kwargs

    def get_forms(self, context_data=None):
        if context_data is None:
            context_data = {}

        if not self.forms:
            kwargs = self.get_form_kwargs()
            data = kwargs.pop("data", None)
            # We don't work with files on those forms
            kwargs.pop("files", None)
            person = kwargs.pop("person")
            kwargs.pop("prefix")
            initial = kwargs.pop("initial")

            got_diploma = data and data.get("got_diploma") in HAS_DIPLOMA_CHOICES
            got_belgian_diploma = got_diploma and data.get("diploma_type") == DiplomaTypes.BELGIAN.name
            got_foreign_diploma = got_diploma and data.get("diploma_type") == DiplomaTypes.FOREIGN.name

            self.forms = {
                "main_form": context_data.pop('form') if 'form' in context_data else self.get_form(),
                "belgian_diploma_form": DoctorateAdmissionEducationBelgianDiplomaForm(
                    person=self.person,
                    prefix="belgian_diploma",
                    initial=initial.get("belgian_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    # don't send data to prevent validation
                    data=data if data and got_belgian_diploma else None,
                    **kwargs,
                ),
                "foreign_diploma_form": DoctorateAdmissionEducationForeignDiplomaForm(
                    prefix="foreign_diploma",
                    initial=initial.get("foreign_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    person=person,
                    # don't send data to prevent validation
                    data=data if data and got_foreign_diploma else None,
                    **kwargs,
                ),
                "schedule_form": DoctorateAdmissionEducationScheduleForm(
                    prefix="schedule",
                    initial=initial.get("belgian_diploma") and initial["belgian_diploma"].get("schedule"),
                    # don't send data to prevent validation
                    data=data if data and got_belgian_diploma else None,
                    empty_permitted=True,
                    use_required_attribute=False,  # for number input that can't be empty
                    **kwargs,
                ),
            }
        return self.forms

    def call_webservice(self, data):
        AdmissionPersonService.update_high_school_diploma(
            self.person,
            data,
            uuid=self.admission_uuid,
        )

    @staticmethod
    def prepare_diploma(data, forms, diploma):
        data[diploma] = forms["{}_form".format(diploma)].cleaned_data
        data[diploma]["academic_graduation_year"] = data.pop("academic_graduation_year")
        data[diploma]["high_school_diploma"] = data.pop("high_school_diploma")
        enrolment_certificate = data.pop("enrolment_certificate")
        data[diploma]["enrolment_certificate"] = (
            enrolment_certificate if data[diploma]["academic_graduation_year"] == get_current_year() else []
        )

    def prepare_data(self, main_form_data):
        # Process the form data to match API
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()

        data = forms["main_form"].cleaned_data

        got_diploma = data.pop("got_diploma")

        if got_diploma == "":
            return {}

        first_cycle_admission_exam = data.pop("first_cycle_admission_exam", [])
        if got_diploma == GotDiploma.NO.name:
            return {
                'high_school_diploma_alternative': {
                    'first_cycle_admission_exam': first_cycle_admission_exam,
                }
            }

        if got_diploma == GotDiploma.THIS_YEAR.name:
            data["academic_graduation_year"] = get_current_year()

        if data.pop("diploma_type") == DiplomaTypes.BELGIAN.name:
            self.prepare_diploma(data, forms, "belgian_diploma")
            schedule = forms.get("schedule_form")
            belgian_diploma = data.get("belgian_diploma")

            if belgian_diploma.get("community") != BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
                data["belgian_diploma"]["educational_type"] = ""
                data["belgian_diploma"]["educational_other"] = ""

            educational_type = belgian_diploma.get("educational_type")

            if educational_type:
                data["belgian_diploma"]["educational_other"] = ""

            if belgian_diploma.pop('other_institute'):
                data["belgian_diploma"]["institute"] = ""
            else:
                data["belgian_diploma"]['other_institute_name'] = ""
                data["belgian_diploma"]['other_institute_address'] = ""

            if schedule and educational_type in EDUCATIONAL_TYPES_REQUIRING_SCHEDULE:
                data["belgian_diploma"]["schedule"] = schedule.cleaned_data

        else:
            self.prepare_diploma(data, forms, "foreign_diploma")
            foreign_diploma_data = data.get("foreign_diploma")
            foreign_diploma_form = forms['foreign_diploma_form']

            is_bachelor = foreign_diploma_data.get("foreign_diploma_type") == ForeignDiplomaTypes.NATIONAL_BACHELOR.name
            is_ue_country = foreign_diploma_form.fields['country'].is_ue_country

            # Clean and define equivalence fields
            foreign_diploma_data["final_equivalence_decision"] = []

            if not is_bachelor:
                foreign_diploma_data["restrictive_equivalence_daes"] = []
                foreign_diploma_data["restrictive_equivalence_admission_test"] = []
            else:
                if not is_ue_country:
                    foreign_diploma_data["final_equivalence_decision"] = foreign_diploma_data[
                        "final_equivalence_decision_not_ue"
                    ]
                elif foreign_diploma_data["equivalence"] == Equivalence.YES.name:
                    foreign_diploma_data["final_equivalence_decision"] = foreign_diploma_data[
                        "final_equivalence_decision_ue"
                    ]

            if not is_bachelor or not is_ue_country:
                foreign_diploma_data["equivalence"] = ''

            if not is_bachelor or not is_ue_country or foreign_diploma_data["equivalence"] != Equivalence.PENDING.name:
                foreign_diploma_data["equivalence_decision_proof"] = []

            foreign_diploma_data.pop("final_equivalence_decision_not_ue")
            foreign_diploma_data.pop("final_equivalence_decision_ue")

            # Clean fields depending on the linguistic regime
            if foreign_diploma_data.get("linguistic_regime"):
                foreign_diploma_data["other_linguistic_regime"] = ""

                if foreign_diploma_data.get("linguistic_regime") in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION:
                    foreign_diploma_data["high_school_transcript_translation"] = []
                    foreign_diploma_data["high_school_diploma_translation"] = []
                    foreign_diploma_data["enrolment_certificate_translation"] = []

            if foreign_diploma_data["academic_graduation_year"] != get_current_year():
                foreign_diploma_data["enrolment_certificate_translation"] = []

        return data
