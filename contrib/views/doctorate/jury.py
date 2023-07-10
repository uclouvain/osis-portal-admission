# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.views.generic import TemplateView, FormView

from admission.contrib.enums import RoleJury
from admission.contrib.forms.jury.membre import JuryMembreForm
from admission.contrib.views.mixins import LoadDoctorateViewMixin

__all__ = [
    'DoctorateAdmissionJuryPreparationDetailView',
    'DoctorateAdmissionJuryDetailView',
]
__namespace__ = False

from admission.services.mixins import WebServiceFormMixin

from admission.services.proposition import AdmissionJuryService, AdmissionCotutelleService, JuryBusinessException


class LoadJuryViewMixin(LoadDoctorateViewMixin):
    """Mixin that can be used to load data for tabs used during the enrolment and eventually after it."""

    @cached_property
    def jury(self):
        return AdmissionJuryService.retrieve_jury(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jury'] = self.jury
        return context


class DoctorateAdmissionJuryPreparationDetailView(LoadJuryViewMixin, TemplateView):
    urlpatterns = 'jury-preparation'
    template_name = 'admission/doctorate/details/jury/preparation.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['cotutelle'] = AdmissionCotutelleService.get_cotutelle(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
        return context_data


class DoctorateAdmissionJuryDetailView(LoadJuryViewMixin, WebServiceFormMixin, FormView):
    urlpatterns = 'jury'
    template_name = 'admission/doctorate/forms/jury/jury.html'
    form_class = JuryMembreForm
    error_mapping = {
        JuryBusinessException.NonDocteurSansJustificationException: "justification_non_docteur",
        JuryBusinessException.MembreExterneSansInstitutionException: "institution",
        JuryBusinessException.MembreExterneSansPaysException: "pays",
        JuryBusinessException.MembreExterneSansNomException: "nom",
        JuryBusinessException.MembreExterneSansPrenomException: "prenom",
        JuryBusinessException.MembreExterneSansTitreException: "titre",
        JuryBusinessException.MembreExterneSansGenreException: "genre",
        JuryBusinessException.MembreExterneSansEmailException: "email",
        JuryBusinessException.MembreDejaDansJuryException: "matricule",
    }

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        membres = AdmissionJuryService.list_jury_members(
            person=self.request.user.person,
            uuid=self.admission_uuid,
        )
        context_data['membres'] = (membre for membre in membres if membre.role == RoleJury.MEMBRE.name)
        context_data['membre_president'] = (membre for membre in membres if membre.role == RoleJury.PRESIDENT.name)
        context_data['membre_secretaire'] = (membre for membre in membres if membre.role == RoleJury.SECRETAIRE.name)
        return context_data

    def call_webservice(self, data):
        return AdmissionJuryService.create_jury_member(
            person=self.person,
            uuid=self.admission_uuid,
            **data,
        )
