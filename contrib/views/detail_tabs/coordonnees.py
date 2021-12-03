# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import get_language
from django.views.generic import TemplateView

from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.services.reference import CountriesService


class DoctorateAdmissionCoordonneesDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'admission/doctorate/detail_coordonnees.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person, uuid=str(self.kwargs['pk']),
        )
        coordonnees = AdmissionPersonService.retrieve_person_coordonnees(self.request.user.person).to_dict()
        context_data['coordonnees'] = coordonnees
        translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'
        if coordonnees['residential'] and coordonnees['residential']['country']:
            residential_country = CountriesService.get_country(
                iso_code=coordonnees['residential']['country'],
                person=self.request.user.person,
            )
            context_data['residential_country'] = getattr(residential_country, translated_field)
        if coordonnees['contact'] and coordonnees['contact']['country']:
            contact_country = CountriesService.get_country(
                iso_code=coordonnees['contact']['country'],
                person=self.request.user.person,
            )
            context_data['contact_country'] = getattr(contact_country, translated_field)
        # check if there is at least one data into contact
        if coordonnees['contact']:
            context_data["show_contact"] = any(v for k, v in coordonnees['contact'].items())
        return context_data
