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
from django.views.generic import RedirectView
from osis_document.api.utils import get_remote_token

from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionPropositionService
from osis_document.utils import get_file_url

__all__ = [
    'AdmissionPDFRecapExportView',
]
__namespace__ = False


class AdmissionPDFRecapExportView(LoadDossierViewMixin, RedirectView):
    urlpatterns = 'pdf-recap'

    service_mapping = {
        'doctorate': AdmissionPropositionService.retrieve_doctorate_education_pdf_recap,
        'general-education': AdmissionPropositionService.retrieve_general_education_pdf_recap,
        'continuing-education': AdmissionPropositionService.retrieve_continuing_education_pdf_recap,
    }

    def get(self, request, *args, **kwargs):
        reading_token = (
            # use the saved pdf if there is one
            get_remote_token(self.admission.pdf_recapitulatif[0])
            if self.admission.pdf_recapitulatif
            # otherwise generate a new pdf
            else self.service_mapping[self.current_context](
                person=self.request.user.person,
                uuid=self.admission_uuid,
            ).token
        )

        self.url = get_file_url(reading_token)

        return super().get(request, *args, **kwargs)
