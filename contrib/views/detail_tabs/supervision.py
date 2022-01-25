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
from django.shortcuts import redirect
from django.views.generic import FormView

from admission.contrib.enums.projet import ChoixStatutProposition
from admission.contrib.enums.supervision import DecisionApprovalEnum
from admission.contrib.forms.supervision import DoctorateAdmissionApprovalForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, AdmissionSupervisionService


class DoctorateAdmissionSupervisionDetailView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_supervision.html'
    form_class = DoctorateAdmissionApprovalForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['admission'].statut != ChoixStatutProposition.SIGNING_IN_PROGRESS.name:
            return redirect('admission:doctorate-update:supervision', **self.kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        )
        context['supervision'] = AdmissionSupervisionService.get_supervision(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        )
        context['approval_form'] = DoctorateAdmissionApprovalForm(self.request.POST or None)
        return context

    def prepare_data(self, data):
        data["matricule"] = self.person.global_id
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the admission is not approved
            data.pop('motif_refus')
        return data

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return AdmissionSupervisionService.approve_proposition(
                person=self.person,
                uuid=str(self.kwargs['pk']),
                **data,
            )
        return AdmissionSupervisionService.reject_proposition(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return self.request.get_full_path()
