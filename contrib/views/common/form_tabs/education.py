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
from django.shortcuts import render
from django.utils.functional import cached_property
from django.views.generic import FormView

from admission.constants import LINGUISTIC_REGIMES_WITHOUT_TRANSLATION, PLUS_5_ISO_CODES
from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaTypes,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
    HAS_DIPLOMA_CHOICES,
)
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms.education import (
    BachelorAdmissionEducationBelgianDiplomaForm,
    BachelorAdmissionEducationForeignDiplomaForm,
    BachelorAdmissionEducationForm,
    BaseAdmissionEducationForm,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import FormMixinWithSpecificQuestions, WebServiceFormMixin
from admission.services.person import (
    ContinuingEducationAdmissionPersonService,
    GeneralEducationAdmissionPersonService,
)
from admission.utils import is_med_dent_training

__all__ = [
    'AdmissionEducationFormView',
]


class AdmissionEducationFormView(FormMixinWithSpecificQuestions, LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/forms/education.html"
    forms = None
    service_mapping = {
        'general-education': GeneralEducationAdmissionPersonService,
        'continuing-education': ContinuingEducationAdmissionPersonService,
    }
    tab_of_specific_questions = Onglets.ETUDES_SECONDAIRES.name

    def get(self, request, *args, **kwargs):
        if not self.admission_uuid:
            # Trick template to not display form and buttons
            context = super(LoadDossierViewMixin, self).get_context_data(form=None, **kwargs)
            return render(request, 'admission/forms/need_training_choice.html', context)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['is_valuated'] = self.high_school_diploma['is_valuated']

        if self.is_bachelor:
            context_data.update(self.get_forms(context_data))
            context_data['form'] = context_data['main_form']  # Trick template to display form tag
            context_data['foreign_diploma_type_images'] = {
                'INTERNATIONAL_BACCALAUREATE': 'admission/images/IBO.png',
                'EUROPEAN_BACHELOR': 'admission/images/schola_europa.png',
            }
            context_data['linguistic_regimes_without_translation'] = LINGUISTIC_REGIMES_WITHOUT_TRANSLATION
            context_data['is_med_dent_training'] = self.is_med_dent_training
            context_data['is_vae_potential'] = self.high_school_diploma['is_vae_potential']
            context_data['plus_5_iso_codes'] = PLUS_5_ISO_CODES
        return context_data

    @cached_property
    def is_bachelor(self):
        return self.admission.formation.type == TrainingType.BACHELOR.name

    @cached_property
    def high_school_diploma(self):
        return (
            self.service_mapping[self.current_context]
            .retrieve_high_school_diploma(
                person=self.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

    def get_template_names(self):
        if self.is_bachelor:
            return ['admission/general_education/forms/bachelor_education.html']
        return ['admission/forms/education.html']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.person
        kwargs["is_valuated"] = self.high_school_diploma["is_valuated"]
        return kwargs

    def get_form_class(self):
        return BachelorAdmissionEducationForm if self.is_bachelor else BaseAdmissionEducationForm

    @cached_property
    def is_med_dent_training(self):
        return is_med_dent_training(self.admission.formation)

    def get_initial(self):
        return {
            **self.high_school_diploma,
            'specific_question_answers': self.admission.reponses_questions_specifiques if self.admission_uuid else {},
        }

    @staticmethod
    def check_bound_and_set_required_attr(form):
        """Check if the passed form is bound. If it is, it means that we can set the use_required_attribute to False
        for form validation."""
        if form.is_bound:
            form.empty_permitted = False

    def post(self, request, *args, **kwargs):
        if not self.is_bachelor or self.high_school_diploma['is_valuated']:
            return super().post(request, *args, **kwargs)

        forms = self.get_forms()

        main_form = forms["main_form"]
        belgian_diploma_form = forms["belgian_diploma_form"]
        foreign_diploma_form = forms["foreign_diploma_form"]

        self.check_bound_and_set_required_attr(belgian_diploma_form)
        self.check_bound_and_set_required_attr(foreign_diploma_form)

        # Page is valid if all bound forms are valid
        if all(not form.is_bound or form.is_valid() for form in forms.values()):
            return self.form_valid(main_form)
        return self.form_invalid(main_form)

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
            kwargs.pop('form_item_configurations')

            graduated_from_high_school = data and data.get("graduated_from_high_school") in HAS_DIPLOMA_CHOICES
            got_belgian_diploma = graduated_from_high_school and data.get("diploma_type") == DiplomaTypes.BELGIAN.name
            got_foreign_diploma = graduated_from_high_school and data.get("diploma_type") == DiplomaTypes.FOREIGN.name

            self.forms = {
                "main_form": context_data.pop('form') if 'form' in context_data else self.get_form(),
                "belgian_diploma_form": BachelorAdmissionEducationBelgianDiplomaForm(
                    person=self.person,
                    prefix="belgian_diploma",
                    initial=initial.get("belgian_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    # don't send data to prevent validation
                    data=data if data and got_belgian_diploma else None,
                    **kwargs,
                ),
                "foreign_diploma_form": BachelorAdmissionEducationForeignDiplomaForm(
                    prefix="foreign_diploma",
                    initial=initial.get("foreign_diploma"),
                    empty_permitted=True,
                    use_required_attribute=False,
                    person=person,
                    is_med_dent_training=self.is_med_dent_training,
                    # don't send data to prevent validation
                    data=data if data and got_foreign_diploma else None,
                    **kwargs,
                ),
            }
        return self.forms

    def call_webservice(self, data):
        self.service_mapping[self.current_context].update_high_school_diploma(
            self.person,
            data,
            uuid=self.admission_uuid,
        )

    @staticmethod
    def prepare_diploma(data, forms, diploma):
        data[diploma] = forms["{}_form".format(diploma)].cleaned_data
        data[diploma]["academic_graduation_year"] = data.get("graduated_from_high_school_year")
        data[diploma]["high_school_diploma"] = data.pop("high_school_diploma")

    def prepare_data(self, main_form_data):
        # General education (except bachelor) and continuing education admission
        if not self.is_bachelor or self.high_school_diploma['is_valuated']:
            return main_form_data

        # Bachelor admission
        forms = self.get_forms()
        for form in forms.values():
            form.is_valid()

        data = forms["main_form"].cleaned_data

        graduated_from_high_school = data.get("graduated_from_high_school")

        if graduated_from_high_school == "":
            return {
                'specific_question_answers': data.get('specific_question_answers'),
            }

        first_cycle_admission_exam = data.pop("first_cycle_admission_exam", [])
        if graduated_from_high_school == GotDiploma.NO.name:
            return {
                'specific_question_answers': data.get('specific_question_answers'),
                'graduated_from_high_school': graduated_from_high_school,
                'graduated_from_high_school_year': data.get('graduated_from_high_school_year'),
                'high_school_diploma_alternative': {'first_cycle_admission_exam': first_cycle_admission_exam},
            }

        # The candidate has a diploma or will have one this year

        if data.pop("diploma_type") == DiplomaTypes.BELGIAN.name:
            self.prepare_diploma(data, forms, "belgian_diploma")
            belgian_diploma = data.get("belgian_diploma")

            if belgian_diploma.get("community") != BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name:
                belgian_diploma["educational_type"] = ""
                belgian_diploma["educational_other"] = ""

            educational_type = belgian_diploma.get("educational_type")

            if educational_type:
                data["belgian_diploma"]["educational_other"] = ""

            if belgian_diploma.pop('other_institute'):
                belgian_diploma["institute"] = ""
            else:
                belgian_diploma['other_institute_name'] = ""
                belgian_diploma['other_institute_address'] = ""

        else:
            self.prepare_diploma(data, forms, "foreign_diploma")
            foreign_diploma_data = data.get("foreign_diploma")
            foreign_diploma_form = forms['foreign_diploma_form']

            is_bachelor = foreign_diploma_data.get("foreign_diploma_type") == ForeignDiplomaTypes.NATIONAL_BACHELOR.name
            equivalence_ue_country = foreign_diploma_form.fields['country'].is_ue_country or self.is_med_dent_training

            # Define and clean main form fields
            # Clean equivalence fields
            if not is_bachelor or not equivalence_ue_country:
                foreign_diploma_data["equivalence"] = ''

            if not is_bachelor or equivalence_ue_country:
                foreign_diploma_data["final_equivalence_decision_not_ue"] = []

            if (
                not is_bachelor
                or not equivalence_ue_country
                or foreign_diploma_data["equivalence"] != Equivalence.PENDING.name
            ):
                foreign_diploma_data["equivalence_decision_proof"] = []

            if (
                not is_bachelor
                or not equivalence_ue_country
                or foreign_diploma_data["equivalence"] != Equivalence.YES.name
            ):
                foreign_diploma_data["final_equivalence_decision_ue"] = []

            # Clean fields depending on the linguistic regime
            if foreign_diploma_data.get("linguistic_regime"):
                foreign_diploma_data["other_linguistic_regime"] = ""

                if foreign_diploma_data.get("linguistic_regime") in LINGUISTIC_REGIMES_WITHOUT_TRANSLATION:
                    foreign_diploma_data["high_school_transcript_translation"] = []
                    foreign_diploma_data["high_school_diploma_translation"] = []

        return data
