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
from osis_education_group_sdk import ApiClient, ApiException
from osis_education_group_sdk.api import trainings_api
from osis_education_group_sdk.model.training_detailed import TrainingDetailed

from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk import education_group as education_group_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers


class EducationGroupAPIClient:
    def __new__(cls):
        api_config = education_group_sdk.build_configuration()
        return trainings_api.TrainingsApi(ApiClient(configuration=api_config))


class TrainingsService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_training(cls, person, year, acronym) -> TrainingDetailed:
        return EducationGroupAPIClient().trainings_read(
            year=year,
            acronym=acronym,
            **build_mandatory_auth_headers(person),
        )
