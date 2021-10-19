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
from osis_reference_sdk import ApiClient
from osis_reference_sdk.api import countries_api, cities_api

from base.models.person import Person
from frontoffice.settings.osis_sdk import reference as reference_sdk


class CountriesAPIClient:
    def __new__(cls, person: Person = None):
        api_config = reference_sdk.build_configuration(person)
        return countries_api.CountriesApi(ApiClient(configuration=api_config))


class CountriesService:
    @classmethod
    def get_countries(cls, *args, **kwargs):
        return CountriesAPIClient().countries_list(*args, **kwargs).results

    @classmethod
    def get_country(cls, *args, **kwargs):
        return CountriesAPIClient().countries_list(*args, **kwargs).results[0]


class CitiesAPIClient:
    def __new__(cls, person: Person = None):
        api_config = reference_sdk.build_configuration(person)
        return cities_api.CitiesApi(ApiClient(configuration=api_config))


class CitiesService:
    @classmethod
    def get_cities(cls, *args, **kwargs):
        return CitiesAPIClient().cities_list(*args, **kwargs)
