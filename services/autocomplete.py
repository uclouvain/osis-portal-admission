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
from osis_admission_sdk import ApiClient

from frontoffice.settings.osis_sdk import admission as admission_sdk
from osis_admission_sdk.api import autocomplete_api


class AdmissionAutocompleteAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return autocomplete_api.AutocompleteApi(ApiClient(configuration=api_config))


class AdmissionAutocompleteService:
    @classmethod
    def autocomplete_sectors(cls):
        return AdmissionAutocompleteAPIClient().list_sector_dtos()

    @classmethod
    def autocomplete_doctorates(cls, sigle):
        return AdmissionAutocompleteAPIClient().list_doctorat_dtos(sigle)

    @classmethod
    def autocomplete_countries(cls):
        return AdmissionAutocompleteAPIClient().list_countries()

    @classmethod
    def autocomplete_zip_codes(cls):
        return AdmissionAutocompleteAPIClient().list_zip_codes().results
