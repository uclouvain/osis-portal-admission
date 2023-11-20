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
from django.views.generic import TemplateView, RedirectView
from osis_document.utils import get_file_url

from admission.contrib.views.mixins import LoadDoctorateViewMixin
from admission.services.doctorate import AdmissionDoctorateService

__all__ = [
    'DoctorateAdmissionConfirmationPaperDetailView',
    'DoctorateAdmissionConfirmationPaperCanvasExportView',
]
__namespace__ = False


class DoctorateAdmissionConfirmationPaperDetailView(LoadDoctorateViewMixin, TemplateView):
    urlpatterns = {'confirmation-paper': 'confirmation'}
    template_name = 'admission/doctorate/details/confirmation_papers.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        all_confirmation_papers = AdmissionDoctorateService.get_confirmation_papers(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

        if all_confirmation_papers:
            context_data['current_confirmation_paper'] = all_confirmation_papers.pop(0)

        context_data['previous_confirmation_papers'] = all_confirmation_papers

        return context_data


class DoctorateAdmissionConfirmationPaperCanvasExportView(LoadDoctorateViewMixin, RedirectView):
    urlpatterns = 'confirmation-paper-canvas'

    def get(self, request, *args, **kwargs):
        from osis_document.api.utils import get_remote_token

        canvas_uuid = AdmissionDoctorateService.get_last_confirmation_paper_canvas(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).uuid

        reading_token = get_remote_token(canvas_uuid)

        self.url = get_file_url(reading_token)

        return super().get(request, *args, **kwargs)
