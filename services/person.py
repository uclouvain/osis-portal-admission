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
from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import person_api


class AdmissionPersonAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return person_api.PersonApi(ApiClient(configuration=api_config))


class AdmissionPersonService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def retrieve_person(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_person_identification_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_person_identification(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person(cls, person, uuid=None, **data):
        if uuid:
            return AdmissionPersonAPIClient().update_person_identification_admission(
                uuid=str(uuid),
                person_identification=data,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().update_person_identification(
            person_identification=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_person_coordonnees(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_coordonnees_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_coordonnees(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person_coordonnees(cls, person, uuid=None, **data):
        if uuid:
            return AdmissionPersonAPIClient().update_coordonnees_admission(
                uuid=str(uuid),
                coordonnees=data,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().update_coordonnees(
            coordonnees=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_high_school_diploma(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_high_school_diploma_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_high_school_diploma(**build_mandatory_auth_headers(person))

    @classmethod
    def update_high_school_diploma(cls, person, data, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().update_high_school_diploma_admission(
                uuid=str(uuid),
                high_school_diploma=data,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().update_high_school_diploma(
            high_school_diploma=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_languages_knowledge(cls, person):
        return AdmissionPersonAPIClient().list_language_knowledges(**build_mandatory_auth_headers(person))

    @classmethod
    def update_languages_knowledge(cls, person, data):
        return AdmissionPersonAPIClient().create_language_knowledge(
            language_knowledge=data,
            **build_mandatory_auth_headers(person),
        )

    # Curriculum
    @classmethod
    def list_curriculum_experiences(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().list_curriculum_experiences_admission(
                uuid=uuid,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().list_curriculum_experiences(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_curriculum_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_curriculum_experience_admission(
                uuid=uuid,
                xp=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_curriculum_experience(
            xp=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum_experience(cls, experience_id, person, data, uuid=None):
        common_params = {
            'xp': experience_id,
            'experience_input': data,
            **build_mandatory_auth_headers(person),
        }
        if uuid:
            return AdmissionPersonAPIClient().update_curriculum_experience_admission(uuid=uuid, **common_params)
        return AdmissionPersonAPIClient().update_curriculum_experience(**common_params)

    @classmethod
    def create_curriculum_experience(cls, person, data, uuid=None):
        common_params = {
            'experience_input': data,
            **build_mandatory_auth_headers(person),
        }

        if uuid:
            return AdmissionPersonAPIClient().create_curriculum_experience_admission(
                uuid=uuid,
                **common_params,
            )
        return AdmissionPersonAPIClient().create_curriculum_experience(**common_params)

    @classmethod
    def delete_curriculum_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().destroy_curriculum_experience_admission(
                uuid=uuid,
                xp=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().destroy_curriculum_experience(
            xp=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_curriculum_file(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_curriculum_file_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_curriculum_file(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum_file(cls, person, data, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().update_curriculum_file_admission(
                uuid=str(uuid),
                curriculum_file=data,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().update_curriculum_file(
            curriculum_file=data,
            **build_mandatory_auth_headers(person),
        )
