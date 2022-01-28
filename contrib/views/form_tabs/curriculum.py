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
from django.shortcuts import resolve_url
from django.views.generic import FormView

from admission.constants import BE_ISO_CODE
from admission.contrib.forms.curriculum import DoctorateAdmissionCurriculumExperienceForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService


class DoctorateAdmissionCurriculumFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = "admission/doctorate/detail_curriculum.html"
    form_class = DoctorateAdmissionCurriculumExperienceForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.request.user.person
        return kwargs

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        proposition_uuid = str(self.kwargs.get("pk", ""))

        context_data["admission"] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )
        context_data["curriculum_experiences"] = AdmissionPersonService.list_curriculum_experiences(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )
        context_data["BE_ISO_CODE"] = BE_ISO_CODE
        return context_data

    # def get
    #
    # def get_initial(self):
    #     curriculum = AdmissionPersonService.retrieve_curriculum(self.request.user.person)
    #     return curriculum.to_dict()["curriculum_years"]
    #

    def prepare_data(self, data):
        # Remove redundant fields
        data.pop('institute_city_be')
        data.pop('activity_institute_city')
        data.pop('activity_institute_name')

        # Format fields values
        data['academic_year'] = int(data['academic_year'])

        return data

    def call_webservice(self, data):
        # breakpoint()
        AdmissionPersonService.create_curriculum_experience(
            person=self.request.user.person,
            uuid=str(self.kwargs.get('pk')),
            data=data,
        )

    def get_success_url(self):
        pk = self.kwargs.get('pk')
        if pk:
            return resolve_url('admission:doctorate-detail:curriculum', pk=pk)
        else:
            return resolve_url('admission:curriculum')


# class DoctorateAdmissionDeleteCurriculumExperienceFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
#     template_name = "admission/doctorate/cancel.html"
#     form_class = Form
#
#     def call_webservice(self, data):
#         AdmissionPropositionService.cancel_proposition(person=self.person, uuid=str(self.kwargs.get('pk')))
#
#     def get_success_url(self):
#         return resolve_url('admission:doctorate-list')
