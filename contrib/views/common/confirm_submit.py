# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import messages
from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from django.views.generic import FormView

from admission.contrib.forms.confirmation import (
    DoctorateAdmissionConfirmationForm,
    DoctorateAdmissionConfirmationWithBelgianDiplomaForm,
)
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import AdmissionPersonService
from admission.services.proposition import (
    AdmissionPropositionService,
    TAB_OF_BUSINESS_EXCEPTION,
)
from admission.templatetags.admission import TAB_TREES

__all__ = [
    'AdmissionConfirmSubmitFormView',
]


class AdmissionConfirmSubmitFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/forms/confirm-submit.html'
    service_mapping = {
        'doctorate': (
            AdmissionPropositionService.verify_proposition,
            AdmissionPropositionService.submit_proposition,
        ),
        'general-education': (
            AdmissionPropositionService.verify_general_proposition,
            AdmissionPropositionService.submit_general_proposition,
        ),
        'continuing-education': (
            AdmissionPropositionService.verify_continuing_proposition,
            AdmissionPropositionService.submit_continuing_proposition,
        ),
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the missing confirmation conditions
        completion_errors = self.service_mapping[self.current_context][0](
            person=self.person,
            uuid=self.admission_uuid,
        )

        # Group the missing conditions by tab if any
        if completion_errors:
            completion_errors_by_tab = {
                tab.name: {'name': tab.label, 'errors': []}
                for child_tabs in TAB_TREES[self.current_context].values()
                for tab in child_tabs
            }

            for error in completion_errors:
                error_tab = TAB_OF_BUSINESS_EXCEPTION[error.status_code]
                completion_errors_by_tab[error_tab]['errors'].append(error.detail)

            context['missing_confirmation_conditions'] = completion_errors_by_tab

        return context

    def check_candidate_has_belgian_diploma(self):
        # Check that the person related to the admission has a belgian diploma
        high_school_diploma = AdmissionPersonService.retrieve_high_school_diploma(
            person=self.person,
            uuid=self.admission_uuid,
        )
        return high_school_diploma.belgian_diploma is not None

    def get_form_class(self):
        if self.current_context == 'doctorate' and self.check_candidate_has_belgian_diploma():
            return DoctorateAdmissionConfirmationWithBelgianDiplomaForm
        return DoctorateAdmissionConfirmationForm

    def get_success_url(self):
        messages.info(self.request, _("Your proposition has been confirmed."))
        return resolve_url(f'admission:{self.current_context}', pk=self.admission_uuid)

    def call_webservice(self, data):
        self.service_mapping[self.current_context][1](
            person=self.person,
            uuid=self.admission_uuid,
        )
