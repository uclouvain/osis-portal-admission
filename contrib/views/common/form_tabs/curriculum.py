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
from django.views.generic import FormView

from admission.contrib.enums.specific_question import Onglets
from admission.contrib.forms.curriculum import (
    ContinuingAdmissionCurriculumFileForm,
    DoctorateAdmissionCurriculumFileForm,
    GeneralAdmissionCurriculumFileForm,
)
from admission.contrib.views.common.detail_tabs.curriculum import AdmissionCurriculumDetailView
from admission.contrib.views.common.form_tabs.curriculum_experiences import AdmissionCurriculumFormMixin
from admission.services.mixins import FormMixinWithSpecificQuestions

__all__ = [
    "AdmissionCurriculumFormView",
]


class AdmissionCurriculumFormView(
    FormMixinWithSpecificQuestions,
    AdmissionCurriculumDetailView,
    AdmissionCurriculumFormMixin,
    FormView,
):
    template_name = 'admission/details/curriculum.html'
    tab_of_specific_questions = Onglets.CURRICULUM.name

    def get_initial(self):
        if self.admission_uuid:
            return self.admission.to_dict()

    def call_webservice(self, data):
        self.service_mapping[self.current_context].update_curriculum(self.person, data, self.admission_uuid)

    def prepare_data(self, data):
        data['uuid_proposition'] = self.admission_uuid
        return data

    def get_form_class(self):
        return {
            'create': DoctorateAdmissionCurriculumFileForm,
            'doctorate': DoctorateAdmissionCurriculumFileForm,
            'general-education': GeneralAdmissionCurriculumFileForm,
            'continuing-education': ContinuingAdmissionCurriculumFileForm,
        }[self.current_context]

    def get_template_names(self):
        return [
            f"admission/{self.formatted_current_context}/forms/curriculum.html",
            'admission/details/curriculum.html',
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.current_context == 'doctorate' or not self.admission_uuid:
            return kwargs
        kwargs['display_equivalence'] = self.display_equivalence
        if self.current_context == 'general-education':
            kwargs['display_curriculum'] = self.display_curriculum
            kwargs['display_bachelor_continuation'] = self.display_bachelor_continuation
            kwargs['display_bachelor_continuation_attestation'] = self.display_bachelor_continuation_attestation
            kwargs['has_belgian_diploma'] = self.has_belgian_diploma
        return kwargs
