# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.views.generic.edit import BaseFormView
from osis_admission_sdk import ApiException

from admission.contrib.enums import (
    ActorType,
    ChoixEtatSignature,
    ChoixStatutPropositionDoctorale,
    DecisionApprovalEnum,
)
from admission.contrib.forms.supervision import (
    DoctorateAdmissionApprovalByPdfForm,
    DoctorateAdmissionApprovalForm,
    DoctorateAdmissionMemberSupervisionForm,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import (
    AdmissionPropositionService,
    AdmissionSupervisionService,
)

__all__ = [
    'DoctorateAdmissionSupervisionDetailView',
    'DoctorateAdmissionRemoveActorView',
    'DoctorateAdmissionSetReferencePromoterView',
    'DoctorateAdmissionApprovalByPdfView',
    'DoctorateAdmissionResendView',
    'DoctorateAdmissionEditExternalMemberView',
    'DoctorateAdmissionSubmitCaView',
]
__namespace__ = False

from osis_admission_sdk.model.actor_type_enum import ActorTypeEnum


class DoctorateAdmissionSupervisionDetailView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'supervision'
    template_name = 'admission/doctorate/forms/supervision.html'
    form_class = DoctorateAdmissionApprovalForm
    rejecting = False

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # If not signing in progress and ability to update supervision, redirect on update page
        if (
            self.admission.statut
            not in [
                ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE.name,
                ChoixStatutPropositionDoctorale.CA_EN_ATTENTE_DE_SIGNATURE.name,
            ]
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
        context['all_approved'] = all(
            signature.get('statut') == ChoixEtatSignature.APPROVED.name
            for signature in self.supervision.get('signatures_promoteurs', [])
            + self.supervision.get('signatures_membres_ca', [])
        )
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
        kwargs['main_namespace'] = self.main_namespace
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
            return resolve_url(f'{self.main_namespace}:supervised-list')
        return self.request.POST.get('redirect_to') or self.request.get_full_path()


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
            'actor_type': ActorTypeEnum(self.kwargs['type']),
            'uuid_membre': self.kwargs['uuid'],
        }

    def call_webservice(self, data):
        AdmissionSupervisionService.remove_member(person=self.person, uuid=self.admission_uuid, **data)

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or self._get_url("supervision")


class DoctorateAdmissionEditExternalMemberView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = {'edit-external-member': 'edit-external-member/<uuid>'}
    form_class = DoctorateAdmissionMemberSupervisionForm

    def prepare_data(self, data):
        return {'uuid_proposition': self.admission_uuid, 'uuid_membre': self.kwargs['uuid'], **data}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['person'] = self.request.user.person
        kwargs['prefix'] = f"member-{self.kwargs['uuid']}"
        return kwargs

    def call_webservice(self, data):
        AdmissionSupervisionService.edit_external_member(person=self.person, uuid=self.admission_uuid, **data)

    def get_success_url(self):
        return self.request.POST.get('redirect_to') or self._get_url("supervision")

    def form_invalid(self, form):
        messages.error(self.request, _("Please correct the errors below"))
        messages.error(self.request, str(form.errors))
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])


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
        return self.request.POST.get('redirect_to') or resolve_url(
            'admission:doctorate:supervision',
            pk=self.kwargs['pk'],
        )

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
        return self.request.POST.get('redirect_to') or resolve_url(
            'admission:doctorate:supervision',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])


class DoctorateAdmissionResendView(LoginRequiredMixin, WebServiceFormMixin, BaseFormView):
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
        return self.request.POST.get('redirect_to') or resolve_url(
            'admission:doctorate:supervision',
            pk=self.kwargs['pk'],
        )

    def form_invalid(self, form):
        messages.error(self.request, '\n'.join(form.errors.get('__all__', [])))
        return redirect('admission:doctorate:supervision', pk=self.kwargs['pk'])


class DoctorateAdmissionSubmitCaView(LoginRequiredMixin, WebServiceFormMixin, SuccessMessageMixin, FormView):
    urlpatterns = 'submit-ca'
    form_class = forms.Form
    success_message = _("Support committee submitted")

    def call_webservice(self, data):
        AdmissionPropositionService.submit_ca(person=self.person, uuid=str(self.kwargs.get('pk')))

    def form_invalid(self, form):
        messages.error(self.request, _("Please first correct the errors"))
        return HttpResponseRedirect(resolve_url("admission:doctorate:supervision", pk=self.kwargs.get('pk')))

    def get_success_url(self):
        return resolve_url("admission:list")
