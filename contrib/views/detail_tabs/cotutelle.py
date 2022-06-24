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
from django.shortcuts import redirect
from django.views.generic import TemplateView

from admission.contrib.enums.doctorat import ChoixStatutDoctorat
from admission.contrib.enums.projet import ChoixStatutProposition
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.proposition import AdmissionCotutelleService


class DoctorateAdmissionCotutelleDetailView(LoadDossierViewMixin, TemplateView):
    template_name = 'admission/doctorate/details/cotutelle.html'

    def get(self, request, *args, **kwargs):
        # Always redirect to update form as long as signatures are not sent
        if (
            self.admission.statut == ChoixStatutProposition.IN_PROGRESS.name
            # we have access if url is present
            and 'url' in self.admission.links['update_cotutelle']
        ):
            return redirect('admission:doctorate:update:cotutelle', **self.kwargs)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['cotutelle'] = AdmissionCotutelleService.get_cotutelle(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).to_dict()
        return context_data
