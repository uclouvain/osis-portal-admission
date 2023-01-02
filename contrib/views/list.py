# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.views.generic import TemplateView

from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import TAB_TREES

__all__ = [
    "AdmissionListView",
    "DoctorateAdmissionMemberListView",
]
__namespace__ = False


class AdmissionListView(LoginRequiredMixin, TemplateView):
    urlpatterns = {'list': ''}
    template_name = "admission/admission_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = AdmissionPropositionService().get_propositions(self.request.user.person)
        context["doctorate_propositions"] = result['doctorate_propositions']
        context["continuing_education_propositions"] = result['continuing_education_propositions']
        context["general_education_propositions"] = result['general_education_propositions']
        context["global_links"] = result['links']
        context["can_create_proposition"] = (
            'url' in result['links']['create_doctorate_proposition']
            or 'url' in result['links']['create_general_proposition']
            or 'url' in result['links']['create_continuing_proposition']
        )
        context["doctorate_tab_tree"] = TAB_TREES['doctorate']
        context["continuing_education_tab_tree"] = TAB_TREES['continuing-education']
        context["general_education_tab_tree"] = TAB_TREES['general-education']
        return context


class DoctorateAdmissionMemberListView(LoginRequiredMixin, TemplateView):
    urlpatterns = {'supervised-list': 'supervised'}
    template_name = "admission/doctorate/supervised_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admissions"] = AdmissionPropositionService().get_supervised_propositions(self.request.user.person)
        context["tab_tree"] = TAB_TREES['doctorate']
        return context
