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
from django.views.generic import TemplateView

from admission.contrib.views.mixins import (
    LoadDossierViewMixin,
    LoadGeneralEducationDossierViewMixin,
    LoadContinuingEducationDossierViewMixin,
)
from admission.services.person import (
    AdmissionPersonService,
    GeneralEducationAdmissionPersonService,
    ContinuingEducationAdmissionPersonService,
)


class AdmissionCoordonneesDetailView(TemplateView):
    template_name = 'admission/doctorate/details/coordonnees.html'
    service = AdmissionPersonService

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        coordonnees = self.service.retrieve_person_coordonnees(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        ).to_dict()
        context_data['coordonnees'] = coordonnees
        # check if there is at least one data into contact
        if coordonnees['contact']:
            context_data["show_contact"] = any(v for k, v in coordonnees['contact'].items())
        return context_data


class DoctorateAdmissionCoordonneesDetailView(
    LoadDossierViewMixin,
    AdmissionCoordonneesDetailView,
):  # pylint: disable=too-many-ancestors
    service = AdmissionPersonService


class GeneralEducationAdmissionCoordonneesDetailView(
    LoadGeneralEducationDossierViewMixin,
    AdmissionCoordonneesDetailView,
):  # pylint: disable=too-many-ancestors
    service = GeneralEducationAdmissionPersonService


class ContinuingEducationAdmissionCoordonneesDetailView(
    LoadContinuingEducationDossierViewMixin,
    AdmissionCoordonneesDetailView,
):  # pylint: disable=too-many-ancestors
    service = ContinuingEducationAdmissionPersonService
