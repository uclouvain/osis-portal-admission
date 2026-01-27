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
from typing import Callable

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import FormView, TemplateView

from admission.constants import (
    DOCUMENTS_REQUEST_JUST_COMPLETED_WITHOUT_DOCUMENT,
    FIELD_REQUIRED_MESSAGE,
)
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.forms.documents import CompleteDocumentsForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionPropositionService
from admission.templatetags.admission import can_update_tab

__all__ = [
    'DocumentsFormView',
    'ConfirmDocumentsFormView',
]


__namespace__ = False


class DocumentsFormView(LoadDossierViewMixin, WebServiceFormMixin, PermissionRequiredMixin, FormView):
    urlpatterns = 'documents'
    template_name = 'admission/forms/documents.html'
    tab_of_specific_questions = Onglets.DOCUMENTS.name
    retrieve_service_mapping = {
        'general-education': AdmissionPropositionService.retrieve_general_education_documents,
        'continuing-education': AdmissionPropositionService.retrieve_continuing_education_documents,
        'doctorate': AdmissionPropositionService.retrieve_doctorate_documents,
    }
    update_service_mapping = {
        'general-education': AdmissionPropositionService.update_general_education_documents,
        'continuing-education': AdmissionPropositionService.update_continuing_education_documents,
        'doctorate': AdmissionPropositionService.update_doctorate_documents,
    }
    give_control_back_to_manager_service_mapping: dict[str, Callable] = {
        'general-education': AdmissionPropositionService.give_control_back_to_general_manager_during_document_request,
        'continuing-education': (
            AdmissionPropositionService.give_control_back_to_continuing_manager_during_document_request
        ),
        'doctorate': AdmissionPropositionService.give_control_back_to_doctorate_manager_during_document_request,
    }
    form_class = CompleteDocumentsForm
    extra_context = {
        'submit_class': 'btn btn-primary',
        'submit_label': gettext_lazy('Send'),
        'submit_icon': 'fa-paper-plane',
    }

    def get(self, request, *args, **kwargs):
        if (
            not self.specific_questions['immediate_requested_documents']
            and not self.specific_questions['later_requested_documents']
        ):
            # No document to submit -> automatically send the admission to the manager and redirect to the list
            self.give_control_back_to_manager_service_mapping[self.current_context](
                person=self.request.user.person,
                uuid=self.admission_uuid,
            )
            self.request.session[DOCUMENTS_REQUEST_JUST_COMPLETED_WITHOUT_DOCUMENT] = True
            return redirect('admission:list')
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        if any(
            FIELD_REQUIRED_MESSAGE in errors
            for field in form.fields['reponses_documents_a_completer__0'].fields
            for errors in getattr(field, 'errors', [])
        ):
            self.error_message = _('Required documents are missing.')
        return super().form_invalid(form)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('admission:list'))
        return super().handle_no_permission()

    def has_permission(self):
        return can_update_tab(admission=self.admission, tab='documents')

    @cached_property
    def specific_questions(self):
        return self.retrieve_service_mapping[self.current_context](
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['deadline'] = self.specific_questions.deadline
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['form_item_configurations'] = [
            self.specific_questions.immediate_requested_documents,
            self.specific_questions.later_requested_documents,
        ]
        return kwargs

    def call_webservice(self, data):
        self.update_service_mapping[self.current_context](
            person=self.person,
            data=data,
            uuid=self.admission_uuid,
        )

    def get_success_url(self):
        # Allow access to the confirm page
        self.request.session['admission_confirm_documents'] = True
        return resolve_url(f'{self.base_namespace}:update:confirm-documents', pk=self.admission_uuid)


class ConfirmDocumentsFormView(LoadDossierViewMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'admission/forms/confirm_documents.html'
    urlpatterns = 'confirm-documents'

    def has_permission(self):
        # Only allow access after a valid submission of the documents completion form
        return self.request.session.pop('admission_confirm_documents', False)
