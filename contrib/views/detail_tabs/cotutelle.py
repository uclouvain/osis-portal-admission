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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from admission.contrib.enums.projet import ChoixStatutProposition
from admission.services.proposition import AdmissionCotutelleService, AdmissionPropositionService


class DoctorateAdmissionCotutelleDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/detail_cotutelle.html'

    def get_admission(self):
        if not hasattr(self, 'admission'):
            self.admission = AdmissionPropositionService.get_proposition(
                person=self.request.user.person,
                uuid=str(self.kwargs['pk']),
            )
        return self.admission

    def get(self, request, *args, **kwargs):
        # Always redirect to update form as long as signatures are not sent
        admission = self.get_admission()
        if (
            admission.statut == ChoixStatutProposition.IN_PROGRESS.name
            and 'url' in admission.links['update_cotutelle']
        ):
            return redirect('admission:doctorate-update:cotutelle', **self.kwargs)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['admission'] = self.get_admission()
        context_data['cotutelle'] = AdmissionCotutelleService.get_cotutelle(
            person=self.request.user.person,
            uuid=str(self.kwargs['pk']),
        ).to_dict()
        return context_data
