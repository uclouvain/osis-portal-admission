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
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from admission.contrib.forms.extension_request import ExtensionRequestForm
from admission.contrib.views.mixins import LoadDoctorateViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.proposition import AdmissionDoctorateService
from osis_admission_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO


class DoctorateAdmissionExtensionRequestFormView(LoadDoctorateViewMixin, WebServiceFormMixin, FormView):
    template_name = 'admission/doctorate/forms/extension_request.html'
    form_class = ExtensionRequestForm
    extra_context = {
        'submit_label': _('Submit my new deadline')
    }

    @cached_property
    def confirmation_paper(self) -> ConfirmationPaperDTO:
        return AdmissionDoctorateService.get_last_confirmation_paper(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_initial(self):
        return (
            {
                'nouvelle_echeance': self.confirmation_paper.demande_prolongation.nouvelle_echeance,
                'justification_succincte': self.confirmation_paper.demande_prolongation.justification_succincte,
                'lettre_justification': self.confirmation_paper.demande_prolongation.lettre_justification,
            }
            if self.confirmation_paper and self.confirmation_paper.demande_prolongation
            else {}
        )

    def call_webservice(self, data):
        AdmissionDoctorateService.submit_confirmation_paper_extension_request(
            person=self.person,
            uuid=self.admission_uuid,
            **data,
        )
