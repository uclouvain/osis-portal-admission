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
from osis_reference_sdk.api import academic_years_api, cities_api, countries_api, languages_api

from frontoffice.settings.osis_sdk import reference as reference_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers


class CountriesAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return countries_api.CountriesApi(ApiClient(configuration=api_config))


class CountriesService:
    @classmethod
    def get_countries(cls, person=None, *args, **kwargs):
        return CountriesAPIClient().countries_list(
            *args,
            **kwargs,
            **build_mandatory_auth_headers(person),
        ).results

    @classmethod
    def get_country(cls, person=None, *args, **kwargs):
        return CountriesAPIClient().countries_list(
            *args,
            **kwargs,
            **build_mandatory_auth_headers(person),
        ).results[0]


class CitiesAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return cities_api.CitiesApi(ApiClient(configuration=api_config))


class CitiesService:
    @classmethod
    def get_cities(cls, person: None, *args, **kwargs):
        return CitiesAPIClient().cities_list(
            *args, **kwargs,
            **build_mandatory_auth_headers(person),
        ).results


class AcademicYearAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return academic_years_api.AcademicYearsApi(ApiClient(configuration=api_config))


class AcademicYearService:
    @classmethod
    def get_academic_years(cls, person):
        return AcademicYearAPIClient().get_academic_years(
            limit=100,
            **build_mandatory_auth_headers(person),
        ).results


class LanguagesAPIClient:
    def __new__(cls):
        api_config = reference_sdk.build_configuration()
        return languages_api.LanguagesApi(ApiClient(configuration=api_config))


class LanguageService:
    @classmethod
    def get_languages(cls, person, *args, **kwargs):
        return LanguagesAPIClient().languages_list(
            limit=100,
            *args,
            **kwargs,
            **build_mandatory_auth_headers(person),
        ).results

    @classmethod
    def get_language(cls, code, person=None):
        # Search is only on name and name_en so we need to iter on whole list to search on code
        languages = cls.get_languages(person)
        return next((lang for lang in languages if lang.code == code), None)  # pragma: no branch
