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
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import resolve_url


# Do not remove the following import as it is used by enum_display templatetag
from django.views.generic import TemplateView
from rest_framework.exceptions import APIException

from admission.contrib.enums.curriculum import *
from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService


class DoctorateAdmissionCurriculumDetailView(LoginRequiredMixin, TemplateView):
    template_name = "admission/doctorate/detail_curriculum.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        proposition_uuid = str(self.kwargs.get("pk", ""))

        context_data["admission"] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )
        # AdmissionPersonService.create_curriculum_experience(
        #     person=self.request.user.person,
        #     uuid=proposition_uuid,
        #     data={
        #         'type': ExperienceTypes.OTHER_OCCUPATIONS.name,
        #         'country': 38,
        #         'academic_year': 2018,
        #     }
        # )
        context_data["curriculum_experiences"] = AdmissionPersonService.list_curriculum_experiences(
            person=self.request.user.person,
            uuid=proposition_uuid,
        )
        return context_data

    def post(self, request, *args, **kwargs):
        if 'confirmed-id' in self.request.POST:
            try:
                AdmissionPersonService.delete_curriculum_experience(
                    experience_id=self.request.POST.get('confirmed-id')[0],
                    person=self.request.user.person,
                    uuid=self.kwargs.get('pk'),
                )
            except APIException:
                messages.error(self.request, _("An error has happened when deleting the experience."))

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        pk = self.kwargs.get('pk')
        if pk:
            return resolve_url('admission:doctorate-detail:curriculum', pk=pk)
        else:
            return resolve_url('admission:curriculum')

