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
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, resolve_url
from django.views.generic import FormView
from django.views.generic.edit import BaseFormView
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.projet import ChoixStatutProposition
from admission.contrib.enums.supervision import DecisionApprovalEnum
from admission.contrib.forms.supervision import DoctorateAdmissionApprovalByPdfForm, DoctorateAdmissionApprovalForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, AdmissionSupervisionService


class DoctorateAdmissionSupervisionDetailView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_supervision.html'
    form_class = DoctorateAdmissionApprovalForm

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # If not signing in progress and ability to update supervision, redirect on update page
        if (
            context['admission'].statut != ChoixStatutProposition.SIGNING_IN_PROGRESS.name
            and 'url' in context['admission'].links['request_signatures']
        ):
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
        context['approve_by_pdf_form'] = DoctorateAdmissionApprovalByPdfForm()
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


class DoctorateAdmissionApprovalByPdfView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    form_class = DoctorateAdmissionApprovalByPdfForm

    def call_webservice(self, data):
        return AdmissionSupervisionService.approve_by_pdf(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate-detail:supervision', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        return redirect('admission:doctorate-detail:supervision', pk=self.kwargs['pk'])
