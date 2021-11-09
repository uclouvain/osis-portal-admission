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
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient

from frontoffice.settings.osis_sdk import admission as admission_sdk
from osis_admission_sdk.api import person_api


class AdmissionPersonAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return person_api.PersonApi(ApiClient(configuration=api_config))


class AdmissionPersonService:
    @classmethod
    def retrieve_person(cls, person):
        return AdmissionPersonAPIClient().retrieve_person_identification(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person(cls, person, **data):
        return AdmissionPersonAPIClient().update_person_identification(
            person_identification=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_person_coordonnees(cls, person):
        return AdmissionPersonAPIClient().retrieve_coordonnees(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person_coordonnees(cls, person, **data):
        return AdmissionPersonAPIClient().update_coordonnees(
            coordonnees=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_curriculum(cls, person):
        return AdmissionPersonAPIClient().retrieve_curriculum(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum(cls, person, **data):
        return AdmissionPersonAPIClient().update_curriculum(
            curriculum=data,
            **build_mandatory_auth_headers(person),
        )
