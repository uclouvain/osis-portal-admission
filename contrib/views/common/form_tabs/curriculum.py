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
    DoctorateAdmissionCurriculumFileForm,
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
    form_class = DoctorateAdmissionCurriculumFileForm
    template_name = 'admission/doctorate/forms/curriculum.html'
    tab_of_specific_questions = Onglets.CURRICULUM.name

    def get_initial(self):
        return {
            'specific_question_answers': self.admission.reponses_questions_specifiques if self.admission_uuid else {},
            'curriculum': self.curriculum.file.get('curriculum'),
        }

    def call_webservice(self, data):
        self.service_mapping[self.current_context].update_curriculum(
            person=self.person,
            data=data,
            uuid=self.admission_uuid,
        )
