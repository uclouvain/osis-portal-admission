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

from django.conf import settings
from django.utils.translation import get_language
from django.views.generic import TemplateView

from admission.services.person import AdmissionPersonService
from admission.services.proposition import AdmissionPropositionService
from admission.services.reference import CountriesService


class DoctorateAdmissionPersonDetailView(TemplateView):
    template_name = 'admission/doctorate/detail_person.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        person = AdmissionPersonService.retrieve_person(self.request.user.person, uuid=self.kwargs.get('uuid'))
        context_data['person'] = person
        context_data['admission'] = AdmissionPropositionService.get_proposition(
            person=self.request.user.person, uuid=str(self.kwargs['pk']),
        )
        context_data['contact_language'] = dict(settings.LANGUAGES).get(person.language)

        translated_field = 'name' if get_language() == settings.LANGUAGE_CODE else 'name_en'
        if person.birth_country:
            birth_country = CountriesService.get_country(
                iso_code=person.birth_country,
                person=self.request.user.person,
            )
            context_data['birth_country'] = getattr(birth_country, translated_field)
        if person.country_of_citizenship:
            country_of_citizenship = CountriesService.get_country(
                iso_code=person.country_of_citizenship,
                person=self.request.user.person,
            )
            context_data['country_of_citizenship'] = getattr(country_of_citizenship, translated_field)
        return context_data
