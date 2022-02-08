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

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

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
            person=self.person,
            uuid=str(self.kwargs['pk']),
        )
        context['supervision'] = AdmissionSupervisionService.get_supervision(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        )
        context['signature_conditions'] = AdmissionSupervisionService.get_signature_conditions(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        )
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        if 'url' not in context['admission'].links['request_signatures']:
            return redirect('admission:doctorate-detail:supervision', **self.kwargs)
        return self.render_to_response(context)

    def prepare_data(self, data):
        return {
            'type': data['type'],
            'member': data['person'] or data['tutor'],
        }

    def call_webservice(self, data):
        return AdmissionSupervisionService.add_member(person=self.person, uuid=str(self.kwargs['pk']), **data)


class DoctorateAdmissionRemoveActorView(LoginRequiredMixin, WebServiceFormMixin, FormView):
    form_class = forms.Form
    template_name = 'admission/doctorate/form_tab_remove_actor.html'
    actor_type_mapping = {
        ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
        ActorType.CA_MEMBER.name: ('signatures_membres_ca', 'membre_ca'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['admission'] = AdmissionPropositionService.get_proposition(
                person=self.person,
                uuid=str(self.kwargs['pk']),
            )
            supervision = AdmissionSupervisionService.get_supervision(person=self.person, uuid=str(self.kwargs['pk']))
            context['member'] = self.get_member(supervision)
        except (ApiException, AttributeError, KeyError):
            raise Http404(_('Member not found'))
        return context

    def get_member(self, supervision):
        collection_name, attr_name = self.actor_type_mapping[self.kwargs['type']]
        for signature in getattr(supervision, collection_name):
            person = getattr(signature, attr_name)
            if person.matricule == self.kwargs['matricule']:
                return person
        raise AttributeError

    def prepare_data(self, data):
        return {
            'type': self.kwargs['type'],
            'member': self.kwargs['matricule'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.remove_member(person=self.person, uuid=str(self.kwargs['pk']), **data)

    def get_success_url(self):
        return resolve_url('admission:doctorate-detail:supervision', pk=self.kwargs['pk'])
