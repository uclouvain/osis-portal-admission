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

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import resolve_url
from django.views.generic import FormView
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.actor import ActorType
from admission.contrib.forms.supervision import DoctorateAdmissionSupervisionForm
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, AdmissionSupervisionService
from osis_admission_sdk import ApiException


class DoctorateAdmissionSupervisionFormView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/form_tab_supervision.html'
    form_class = DoctorateAdmissionSupervisionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        )
        return context

    def prepare_data(self, data):
        return {
            'type': data['type'],
            'member': data['person'] or data['tutor'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.add_member(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )


class DoctorateAdmissionRemoveActorView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    form_class = forms.Form
    template_name = 'admission/doctorate/form_tab_remove_actor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['admission'] = AdmissionPropositionService.get_proposition(
                person=self.request.user.person,
                uuid=str(self.kwargs['pk']),
            )
            supervision = AdmissionSupervisionService.get_supervision(
                person=self.request.user.person,
                uuid=str(self.kwargs['pk']),
            )
            type_mapping = {
                ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
                ActorType.CA_MEMBER.name: ('signatures_membres_ca', 'membre_ca'),
            }
            match = type_mapping[self.kwargs['type']]
            signature = next(m for m in getattr(supervision, match[0]))
            context['member'] = getattr(signature, match[1])
        except (ApiException, AttributeError):
            raise Http404(_('Member not found'))
        return context

    def prepare_data(self, data):
        return {
            'type': self.kwargs['type'],
            'member': self.kwargs['matricule'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.remove_member(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate-detail:supervision', pk=self.kwargs['pk'])
