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
import osis_learning_unit_sdk
from osis_learning_unit_sdk.api import learning_units_api

from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk import admission as admission_sdk, learning_unit as learning_unit_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import autocomplete_api


class AdmissionAutocompleteAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return autocomplete_api.AutocompleteApi(ApiClient(configuration=api_config))


class AdmissionAutocompleteService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_sectors(cls, person=None):
        return AdmissionAutocompleteAPIClient().list_sector_dtos(**build_mandatory_auth_headers(person))

    @classmethod
    def get_doctorates(cls, person=None, sigle=""):
        return AdmissionAutocompleteAPIClient().list_doctorat_dtos(sigle, **build_mandatory_auth_headers(person))

    @classmethod
    def autocomplete_tutors(cls, person, **kwargs):
        return AdmissionAutocompleteAPIClient().list_tutors(
            **kwargs,
            **build_mandatory_auth_headers(person),
        )['results']

    @classmethod
    def autocomplete_persons(cls, person, **kwargs):
        return AdmissionAutocompleteAPIClient().list_persons(
            **kwargs,
            **build_mandatory_auth_headers(person),
        )['results']

    @classmethod
    def autocomplete_learning_unit_years(cls, year, acronym_search, person):
        configuration = learning_unit_sdk.build_configuration()
        with osis_learning_unit_sdk.ApiClient(configuration) as api_client:
            api_instance = learning_units_api.LearningUnitsApi(api_client)
        return api_instance.learningunits_list(
            year=int(year),
            acronym_like=acronym_search,
            **build_mandatory_auth_headers(person),
        )['results']
