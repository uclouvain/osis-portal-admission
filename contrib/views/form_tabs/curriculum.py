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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView

from admission.contrib.forms.curriculum import DoctorateAdmissionCurriculumFormSet
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService


class DoctorateAdmissionCurriculumFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/form_tab_curriculum.html"
    form_class = DoctorateAdmissionCurriculumFormSet

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["form_kwargs"] = {"person": self.request.user.person}
        return kwargs

    def get_initial(self):
        curriculum = AdmissionPersonService.retrieve_curriculum(self.request.user.person)
        return curriculum.to_dict()["curriculum_years"]

    def prepare_data(self, data):
        return data  # TODO merge all the year with their experiences

    def call_webservice(self, data):
        AdmissionPersonService.update_curriculum(person=self.request.user.person, **data)
