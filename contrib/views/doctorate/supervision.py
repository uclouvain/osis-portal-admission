# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.edit import BaseFormView

from admission.contrib.enums import ActorType, ChoixStatutProposition, DecisionApprovalEnum
from admission.contrib.forms.supervision import DoctorateAdmissionApprovalByPdfForm, DoctorateAdmissionApprovalForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService, AdmissionSupervisionService
from osis_admission_sdk import ApiException

__all__ = [
    'DoctorateAdmissionSupervisionDetailView',
    'DoctorateAdmissionRemoveActorView',
    'DoctorateAdmissionSetReferencePromoterView',
    'DoctorateAdmissionApprovalByPdfView',
    'DoctorateAdmissionExternalResendView',
]
__namespace__ = False


class DoctorateAdmissionSupervisionDetailView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'supervision'
    template_name = 'admission/doctorate/forms/supervision.html'
    form_class = DoctorateAdmissionApprovalForm
    rejecting = False

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # If not signing in progress and ability to update supervision, redirect on update page
        if (
            self.admission.statut != ChoixStatutProposition.SIGNING_IN_PROGRESS.name
            and 'url' in self.admission.links['request_signatures']
        ):
            return redirect('admission:doctorate:update:supervision', **self.kwargs)
        return self.render_to_response(context)

    @cached_property
    def supervision(self):
        return AdmissionSupervisionService.get_supervision(
            person=self.person,
            uuid=self.admission_uuid,
        ).to_dict()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supervision'] = self.supervision
        context['approve_by_pdf_form'] = DoctorateAdmissionApprovalByPdfForm()
        context['approval_form'] = context.pop('form')  # Trick template to remove save button
        return context

    def get_initial(self):
        return {
            'institut_these': self.admission.institut_these,
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.person
        kwargs['include_institut_these'] = (
            # User is the reference promoter
            self.get_current_member_uuid() == self.supervision['promoteur_reference']
            # institut_these is not yet set
            and not self.admission.institut_these
        )
        return kwargs

    def prepare_data(self, data):
        data["uuid_membre"] = self.get_current_member_uuid()
        if data.get('decision') == DecisionApprovalEnum.APPROVED.name:
            # The reason is useful only if the admission is not approved
            data.pop('motif_refus')
        return data

    def get_current_member_uuid(self):
        return next(
            iter(
                [
                    signature['promoteur']['uuid']
                    for signature in self.supervision['signatures_promoteurs']
                    if self.person.global_id == signature['promoteur']['matricule']
                ]
                + [
                    signature['membre_ca']['uuid']
                    for signature in self.supervision['signatures_membres_ca']
                    if self.person.global_id == signature['membre_ca']['matricule']
                ]
            ),
            None,
        )

    def call_webservice(self, data):
        decision = data.pop('decision')
        if decision == DecisionApprovalEnum.APPROVED.name:
            return AdmissionSupervisionService.approve_proposition(
                person=self.person,
                uuid=self.admission_uuid,
                **data,
            )
        self.rejecting = True
        return AdmissionSupervisionService.reject_proposition(
            person=self.person,
            uuid=self.admission_uuid,
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("Your decision has been saved."))
        if (
            self.person.global_id
            in [signature['membre_ca']['matricule'] for signature in self.supervision['signatures_membres_ca']]
            and self.rejecting
        ):
            try:
                AdmissionPropositionService().get_supervised_propositions(self.request.user.person)
            except PermissionDenied:
                # That may be the last admission the member has access to, if so, redirect to homepage
                return resolve_url('home')
            # Redirect on list
            return resolve_url('admission:supervised-list')
        return self.request.get_full_path()


class DoctorateAdmissionRemoveActorView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'remove-actor': 'remove-member/<type>/<uuid>'}
    form_class = forms.Form
    template_name = 'admission/doctorate/forms/remove_actor.html'
    actor_type_mapping = {
        ActorType.PROMOTER.name: ('signatures_promoteurs', 'promoteur'),
        ActorType.CA_MEMBER.name: ('signatures_membres_ca', 'membre_ca'),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            supervision = AdmissionSupervisionService.get_supervision(
                person=self.person,
                uuid=self.admission_uuid,
            ).to_dict()
            context['member'] = self.get_member(supervision)
        except (ApiException, AttributeError, KeyError):
            raise Http404(_('Member not found'))
        context['force_form'] = True
        return context

    def get_member(self, supervision):
        collection_name, attr_name = self.actor_type_mapping[self.kwargs['type']]
        for signature in supervision[collection_name]:
            member = signature[attr_name]
            if member['uuid'] == self.kwargs['uuid']:
                return member
        raise KeyError

    def prepare_data(self, data):
        return {
            'type': self.kwargs['type'],
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.remove_member(person=self.person, uuid=self.admission_uuid, **data)

    def get_success_url(self):
        return self._get_url("supervision")


class DoctorateAdmissionSetReferencePromoterView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = {'set-reference-promoter': 'set-reference-promoter/<uuid>'}
    form_class = forms.Form

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['pk']),
            'uuid_promoteur': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.set_reference_promoter(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])


class DoctorateAdmissionApprovalByPdfView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = 'approve-by-pdf'
    form_class = DoctorateAdmissionApprovalByPdfForm

    def call_webservice(self, data):
        return AdmissionSupervisionService.approve_by_pdf(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        return resolve_url('admission:doctorate:supervision', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])


class DoctorateAdmissionExternalResendView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
    urlpatterns = {'resend-invite': 'resend-invite/<uuid>'}
    template_name = 'admission/doctorate/forms/external_confirm.html'
    form_class = forms.Form

    def prepare_data(self, data):
        return {
            'uuid_proposition': str(self.kwargs['pk']),
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.resend_invite(
            person=self.person,
            uuid=str(self.kwargs['pk']),
            **data,
        )

    def get_success_url(self):
        messages.info(self.request, _("An invitation has been sent again."))
        return resolve_url('admission:doctorate:supervision', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])
