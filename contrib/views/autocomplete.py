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

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import get_language
from osis_organisation_sdk.model.entite_type_enum import EntiteTypeEnum

from admission.constants import BE_ISO_CODE
from admission.services.autocomplete import AdmissionAutocompleteService
from admission.services.organisation import EntitiesService
from admission.services.reference import CitiesService, CountriesService, LanguageService
from admission.utils import format_entity_address, format_entity_title

__all__ = [
    "DoctorateAutocomplete",
    "CountryAutocomplete",
    "CityAutocomplete",
    "LanguageAutocomplete",
    "TutorAutocomplete",
    "PersonAutocomplete",
    "InstituteAutocomplete",
    "InstituteLocationAutocomplete",
]

from base.models.enums.entity_type import INSTITUTE


class DoctorateAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService.get_doctorates(self.request.user.person, self.forwarded['sector'])

    def results(self, results):
        return [
            dict(
                id="{result.sigle}-{result.annee}".format(result=result),
                sigle=result.sigle,
                sigle_entite_gestion=result.sigle_entite_gestion,
                text="{sigle} - {intitule}".format(sigle=result.sigle, intitule=result.intitule),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        """Return list of strings that match the autocomplete query."""
        return [
            x
            for x in results
            if self.q.lower() in "{sigle} - {intitule}".format(sigle=x.sigle, intitule=x.intitule).lower()
        ]


class CountryAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return CountriesService.get_countries(person=self.request.user.person, search=self.q)

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=country.iso_code,
                text=country.name if get_language() == settings.LANGUAGE_CODE else country.name_en,
                european_union=country.european_union,
            )
            for country in results
            if not self.forwarded.get('exclude_be', False) or country.iso_code != BE_ISO_CODE
        ]


class CityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return CitiesService.get_cities(
            person=self.request.user.person,
            search=self.q,
            zip_code=self.forwarded.get('postal_code', ''),
        )

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        """Return the result dictionary."""
        return [dict(id=city.name, text=city.name) for city in results]


class LanguageAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return LanguageService.get_languages(person=self.request.user.person, search=self.q)

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=language.code,
                text=language.name if get_language() == settings.LANGUAGE_CODE else language.name_en,
            )
            for language in results
        ]


class TutorAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_tutors(
            person=self.request.user.person,
            search=self.q,
        )

    def results(self, results):
        return [
            dict(
                id=result.global_id,
                text="{result.first_name} {result.last_name}".format(result=result),
            )
            for result in results
        ]

    def autocomplete_results(self, results):
        return results


class PersonAutocomplete(TutorAutocomplete):
    def get_list(self):
        return AdmissionAutocompleteService.autocomplete_persons(
            person=self.request.user.person,
            search=self.q,
        )


class InstituteAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        # Return a list of UCL institutes whose title / acronym is specified by the user
        return EntitiesService.get_ucl_entities(
            limit=10,
            person=self.request.user.person,
            entity_type=[
                EntiteTypeEnum(INSTITUTE),
            ],
            search=self.q,
        )

    def autocomplete_results(self, results):
        return results

    def results(self, results):
        return [
            dict(
                id=entity.uuid,
                text=format_entity_title(entity=entity),
            )
            for entity in results
        ]


class InstituteLocationAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        # Return a list of addresses related to the thesis institute, if defined
        if not self.forwarded['institut_these']:
            return []
        return EntitiesService.get_ucl_entity_addresses(
            person=self.request.user.person,
            uuid=self.forwarded['institut_these'],
        )

    def results(self, results):
        formatted_results = []
        for address in results:
            formatted_address = format_entity_address(address)
            formatted_results.append({'id': formatted_address, 'text': formatted_address})
        return formatted_results
