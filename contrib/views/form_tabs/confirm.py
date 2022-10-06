# #
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
from admission.templatetags.admission import get_subtab_label


class DoctorateAdmissionConfirmFormView(
    LoadDossierViewMixin,
    WebServiceFormMixin,
    FormView,
):  # pylint: disable=too-many-ancestors
    template_name = 'admission/doctorate/forms/confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Retrieve the missing confirmation conditions
        proposition_completion_errors = AdmissionPropositionService.verify_proposition(
            person=self.person,
            uuid=self.admission_uuid,
        )

        # Group the missing conditions by tab if any
        if proposition_completion_errors:

            proposition_completion_errors_by_tab = {
                tab: {'name': get_subtab_label(tab, 'doctorate'), 'errors': []}
                for tab in [
                    'person',
                    'coordonnees',
                    'education',
                    'curriculum',
                    'languages',
                    'project',
                    'cotutelle',
                    'supervision',
                    'accounting',
                ]
            }

            for error in proposition_completion_errors:
                proposition_completion_errors_by_tab[TAB_OF_BUSINESS_EXCEPTION[error.status_code]]['errors'].append(
                    error.detail
                )

            context['missing_confirmation_conditions'] = proposition_completion_errors_by_tab

        return context

    def check_candidate_has_belgian_diploma(self):
        # Check that the person related to the admission has a belgian diploma
        high_school_diploma = AdmissionPersonService.retrieve_high_school_diploma(
            person=self.person,
            uuid=self.admission_uuid,
        )
        return high_school_diploma.belgian_diploma is not None

    def get_form_class(self):
        if self.check_candidate_has_belgian_diploma():
            return DoctorateAdmissionConfirmationWithBelgianDiplomaForm
        else:
            return DoctorateAdmissionConfirmationForm

    def get_success_url(self):
        messages.info(self.request, _("Your proposition has been confirmed."))
        return resolve_url('admission:doctorate:project', pk=self.admission_uuid)

    def call_webservice(self, data):
        AdmissionPropositionService.submit_proposition(
            person=self.person,
            uuid=self.admission_uuid,
        )
