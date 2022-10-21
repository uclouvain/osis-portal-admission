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
from django.utils.functional import cached_property
from django.views.generic.base import ContextMixin

from admission.contrib.enums.projet import ChoixStatutProposition
from admission.services.proposition import AdmissionPropositionService
from admission.services.doctorate import AdmissionDoctorateService


class LoadViewMixin(LoginRequiredMixin, ContextMixin):
    @cached_property
    def admission_uuid(self):
        return str(self.kwargs.get('pk', ''))

    @cached_property
    def admission(self):
        return AdmissionPropositionService.get_proposition(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    @cached_property
    def doctorate(self):
        return AdmissionDoctorateService.get_doctorate(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )


class LoadDossierViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.admission_uuid:
            context['admission'] = self.admission
            if self.admission.statut == ChoixStatutProposition.ENROLLED.name:
                context['doctorate'] = self.doctorate
                # We display the information related to the doctorate instead of the admission
                context['detail_base_template'] = 'admission/doctorate/details/doctorate_tab_layout.html'

        return context


class LoadDoctorateViewMixin(LoadViewMixin):
    """Mixin that can be used to load data for tabs used after the enrolment."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.admission_uuid:
            context['doctorate'] = self.doctorate

        return context
