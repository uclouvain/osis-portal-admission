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

from admission.contrib.enums.supervision import DecisionApprovalEnum
from admission.contrib.forms.supervision import DoctorateAdmissionApprovalForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, AdmissionSupervisionService


class DoctorateAdmissionSupervisionDetailView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/detail_supervision.html'
    form_class = DoctorateAdmissionApprovalForm
    is_detail_view = True

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=self.kwargs['pk'],
        )
        context_data['supervision'] = AdmissionSupervisionService.get_supervision(
            person=self.request.user.person,
            uuid=self.kwargs['pk'],
        )
        return context_data

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return AdmissionSupervisionService.approve_proposition(
                person=self.person,
                uuid=self.kwargs['pk'],
                approuver_proposition_command={
                    "commentaire_interne": data['internal_comment'],
                    "commentaire_externe": data['comment'],
                    "matricule": self.person.global_id
                },
            )
        else:
            return AdmissionSupervisionService.reject_proposition(
                person=self.person,
                uuid=self.kwargs['pk'],
                refuser_proposition_command={
                    "commentaire_interne": data['internal_comment'],
                    "commentaire_externe": data['comment'],
                    "matricule": self.person.global_id,
                    "motif_refus": data['rejection_reason'],
                },
            )
