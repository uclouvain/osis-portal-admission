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

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import get_language

from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.reference import CitiesService, CountriesService, LanguageService

__all__ = [
    "DoctorateAutocomplete",
    "CountryAutocomplete",
    "CityAutocomplete",
    "LanguageAutocomplete",
    "TutorAutocomplete",
    "PersonAutocomplete",
]


class DoctorateAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService.get_doctorates(self.request.user.person, self.forwarded['sector'])

    def results(self, results):
        return [dict(
            id="{result.sigle}-{result.annee}".format(result=result),
            sigle_entite_gestion=result.sigle_entite_gestion,
            text="{sigle} - {intitule}".format(
                sigle=result.sigle,
                intitule=result.intitule_fr if get_language() == settings.LANGUAGE_CODE else result.intitule_en,
            )
        ) for result in results]

    def autocomplete_results(self, results):
        """Return list of strings that match the autocomplete query."""
        return [x for x in results if self.q.lower() in "{sigle} - {intitule}".format(
            sigle=x.sigle,
            intitule=x.intitule_fr if get_language() == settings.LANGUAGE_CODE else x.intitule_en,
        ).lower()]


class CountryAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return CountriesService.get_countries(person=self.request.user.person)

    def autocomplete_results(self, results):
        return CountriesService.get_countries(person=self.request.user.person, search=self.q)

    def results(self, results):
        return [dict(
            id=country.iso_code,
            text=country.name_en if settings.LANGUAGE_CODE == 'en' else country.name,
        ) for country in results]


class CityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return CitiesService.get_cities(
            person=self.request.user.person,
            zip_code=self.forwarded['postal_code'],
        )

    def autocomplete_results(self, results):
        """Return list of strings that match the autocomplete query."""
        return CitiesService.get_cities(
            person=self.request.user.person,
            zip_code=self.forwarded['postal_code'],
            search=self.q,
        )

    def results(self, results):
        """Return the result dictionary."""
        return [dict(id=city.name, text=city.name) for city in results]


class LanguageAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return LanguageService.get_languages(person=self.request.user.person)

    def autocomplete_results(self, results):
        return LanguageService.get_languages(person=self.request.user.person, search=self.q)

    def results(self, results):
        return [dict(id=language.code, text=language.name) for language in results]


class TutorAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_tutors(
            person=self.request.user.person,
            search=(self.request.GET.get('q', '')),
        )

    def results(self, results):
        return [dict(
            id=result.global_id,
            text="{result.first_name} {result.last_name}".format(result=result)
        ) for result in results]

    def autocomplete_results(self, results):
        return results


class PersonAutocomplete(TutorAutocomplete):
    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_persons(
            person=self.request.user.person,
            search=self.request.GET.get('q', ''),
        )
