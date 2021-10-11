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

__all__ = [
    "SectorAutocomplete",
    "DoctorateAutocomplete",
    "CityAutocomplete",
]


class SectorAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService().autocomplete_sectors()

    def results(self, results):
        return [dict(
            id=result.sigle,
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


class DoctorateAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService().autocomplete_doctorates(self.forwarded['sector'])

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


class CityAutocomplete(LoginRequiredMixin, autocomplete.Select2ListView):
    def get_list(self):
        return AdmissionAutocompleteService().autocomplete_zip_codes()

    def results(self, results):
        """Return the result dictionary."""
        return [dict(
            name=city.name,
            country_iso_code=city.country_iso_code,
            zip_code=city.zip_code,
        ) for city in results]

    def autocomplete_results(self, results):
        """Return list of strings that match the autocomplete query."""
        return [city for city in results if self.q.lower() in "{name} - {country_iso_code} - {zip_code}".format(
            name=city.name,
            country_iso_code=city.country_iso_code,
            zip_code=city.zip_code,
        ).lower()]
