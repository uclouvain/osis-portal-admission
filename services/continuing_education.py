# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import continuing_education_api
from osis_admission_sdk.model.informations_specifiques_formation_continue_dto import (
    InformationsSpecifiquesFormationContinueDTO,
)

from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers


class ContinuingEducationAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return continuing_education_api.ContinuingEducationApi(ApiClient(configuration=api_config))


class ContinuingEducationService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_continuing_education_information(
        cls,
        person,
        acronym: str,
        year: int,
    ) -> InformationsSpecifiquesFormationContinueDTO:
        return ContinuingEducationAPIClient().retrieve_informations_specifiques_formation_continue_dto(
            sigle=acronym,
            annee=year,
            **build_mandatory_auth_headers(person),
        )
