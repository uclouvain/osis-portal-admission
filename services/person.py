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
from osis_admission_sdk.api import person_api
from osis_admission_sdk.model.identification_dto import IdentificationDTO
from osis_admission_sdk.model.person_identification import PersonIdentification

from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers


class AdmissionPersonAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return person_api.PersonApi(ApiClient(configuration=api_config))


class AdmissionPersonService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    # Identification
    @classmethod
    def retrieve_identification_dto(cls, person) -> IdentificationDTO:
        return AdmissionPersonAPIClient().retrieve_identification_dto(
            **build_mandatory_auth_headers(person),
        )

    # Person
    @classmethod
    def retrieve_person(cls, person, uuid=None) -> PersonIdentification:
        if uuid:
            return AdmissionPersonAPIClient().retrieve_person_identification_admission(
                uuid=str(uuid),
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_person_identification(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person(cls, person, data, uuid=None):
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

    # Coordinates
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
    def update_person_coordonnees(cls, person, data, uuid=None):
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

    # Education
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

    # Languages
    @classmethod
    def retrieve_languages_knowledge(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().list_language_knowledges_admission(
                **build_mandatory_auth_headers(person),
                uuid=str(uuid),
            )
        return AdmissionPersonAPIClient().list_language_knowledges(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_languages_knowledge(cls, person, data, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().create_language_knowledge_admission(
                uuid=str(uuid),
                language_knowledge=data,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().create_language_knowledge(
            language_knowledge=data,
            **build_mandatory_auth_headers(person),
        )

    # Curriculum
    @classmethod
    def get_curriculum(cls, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_curriculum_details_admission(
                uuid=uuid,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_curriculum_details(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_professional_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_professional_experience_admission(
                uuid=uuid,
                experience_id=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_professional_experience(
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_professional_experience(cls, experience_id, person, data, uuid=None):
        common_params = {
            'experience_id': experience_id,
            'professional_experience': data,
            **build_mandatory_auth_headers(person),
        }
        if uuid:
            return AdmissionPersonAPIClient().update_professional_experience_admission(uuid=uuid, **common_params)
        return AdmissionPersonAPIClient().update_professional_experience(**common_params)

    @classmethod
    def create_professional_experience(cls, person, data, uuid=None):
        common_params = {
            'professional_experience': data,
            **build_mandatory_auth_headers(person),
        }

        if uuid:
            return AdmissionPersonAPIClient().create_professional_experience_admission(uuid=uuid, **common_params)
        return AdmissionPersonAPIClient().create_professional_experience(**common_params)

    @classmethod
    def delete_professional_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().destroy_professional_experience_admission(
                uuid=uuid,
                experience_id=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().destroy_professional_experience(
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_educational_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().retrieve_educational_experience_admission(
                uuid=uuid,
                experience_id=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().retrieve_educational_experience(
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_educational_experience(cls, experience_id, person, data, uuid=None):
        common_params = {
            'experience_id': experience_id,
            'educational_experience': data,
            **build_mandatory_auth_headers(person),
        }
        if uuid:
            return AdmissionPersonAPIClient().update_educational_experience_admission(uuid=uuid, **common_params)
        return AdmissionPersonAPIClient().update_educational_experience(**common_params)

    @classmethod
    def create_educational_experience(cls, person, data, uuid=None):
        common_params = {
            'educational_experience': data,
            **build_mandatory_auth_headers(person),
        }

        if uuid:
            return AdmissionPersonAPIClient().create_educational_experience_admission(uuid=uuid, **common_params)
        return AdmissionPersonAPIClient().create_educational_experience(**common_params)

    @classmethod
    def delete_educational_experience(cls, experience_id, person, uuid=None):
        if uuid:
            return AdmissionPersonAPIClient().destroy_educational_experience_admission(
                uuid=uuid,
                experience_id=experience_id,
                **build_mandatory_auth_headers(person),
            )
        return AdmissionPersonAPIClient().destroy_educational_experience(
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_doctorat_completer_curriculum_command_admission(
            uuid=uuid,
            doctorat_completer_curriculum_command=data,
            **build_mandatory_auth_headers(person),
        )


class GeneralEducationAdmissionPersonService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    # Person
    @classmethod
    def retrieve_person(cls, person, uuid) -> PersonIdentification:
        return AdmissionPersonAPIClient().retrieve_person_identification_general_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person(cls, person, uuid, data):
        return AdmissionPersonAPIClient().update_person_identification_general_education_admission(
            uuid=uuid,
            person_identification=data,
            **build_mandatory_auth_headers(person),
        )

    # Coordinates
    @classmethod
    def retrieve_person_coordonnees(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_coordonnees_general_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person_coordonnees(cls, person, uuid, data):
        return AdmissionPersonAPIClient().update_coordonnees_general_education_admission(
            uuid=uuid,
            coordonnees=data,
            **build_mandatory_auth_headers(person),
        )

    # Education
    @classmethod
    def retrieve_high_school_diploma(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_high_school_diploma_general_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_high_school_diploma(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_high_school_diploma_general_education_admission(
            uuid=uuid,
            high_school_diploma=data,
            **build_mandatory_auth_headers(person),
        )

    # Exam
    @classmethod
    def retrieve_exam(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_exam_general_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_exam(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_exam_general_education_admission(
            uuid=uuid,
            exam=data,
            **build_mandatory_auth_headers(person),
        )

    # Curriculum
    @classmethod
    def get_curriculum(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_curriculum_details_general_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_professional_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().retrieve_professional_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_professional_experience(cls, experience_id, person, data, uuid):
        return AdmissionPersonAPIClient().update_professional_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            professional_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_professional_experience(cls, person, data, uuid):
        return AdmissionPersonAPIClient().create_professional_experience_general_education_admission(
            uuid=uuid,
            professional_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def delete_professional_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().destroy_professional_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_educational_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().retrieve_educational_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_educational_experience(cls, experience_id, person, data, uuid):
        return AdmissionPersonAPIClient().update_educational_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            educational_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_educational_experience(cls, person, data, uuid):
        return AdmissionPersonAPIClient().create_educational_experience_general_education_admission(
            uuid=uuid,
            educational_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def delete_educational_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().destroy_educational_experience_general_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_general_education_completer_curriculum_command_admission(
            uuid=uuid,
            general_education_completer_curriculum_command=data,
            **build_mandatory_auth_headers(person),
        )


class ContinuingEducationAdmissionPersonService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    # Person
    @classmethod
    def retrieve_person(cls, person, uuid) -> PersonIdentification:
        return AdmissionPersonAPIClient().retrieve_person_identification_continuing_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person(cls, person, uuid, data):
        return AdmissionPersonAPIClient().update_person_identification_continuing_education_admission(
            uuid=uuid,
            person_identification=data,
            **build_mandatory_auth_headers(person),
        )

    # Coordinates
    @classmethod
    def retrieve_person_coordonnees(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_coordonnees_continuing_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_person_coordonnees(cls, person, uuid, data):
        return AdmissionPersonAPIClient().update_coordonnees_continuing_education_admission(
            uuid=uuid,
            coordonnees=data,
            **build_mandatory_auth_headers(person),
        )

    # Education
    @classmethod
    def retrieve_high_school_diploma(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_high_school_diploma_continuing_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_high_school_diploma(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_high_school_diploma_continuing_education_admission(
            uuid=uuid,
            high_school_diploma=data,
            **build_mandatory_auth_headers(person),
        )

    # Curriculum
    @classmethod
    def get_curriculum(cls, person, uuid):
        return AdmissionPersonAPIClient().retrieve_curriculum_details_continuing_education_admission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_professional_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().retrieve_professional_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_professional_experience(cls, experience_id, person, data, uuid):
        return AdmissionPersonAPIClient().update_professional_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            professional_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_professional_experience(cls, person, data, uuid):
        return AdmissionPersonAPIClient().create_professional_experience_continuing_education_admission(
            uuid=uuid,
            professional_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def delete_professional_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().destroy_professional_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_educational_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().retrieve_educational_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_educational_experience(cls, experience_id, person, data, uuid):
        return AdmissionPersonAPIClient().update_educational_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            educational_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_educational_experience(cls, person, data, uuid):
        return AdmissionPersonAPIClient().create_educational_experience_continuing_education_admission(
            uuid=uuid,
            educational_experience=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def delete_educational_experience(cls, experience_id, person, uuid):
        return AdmissionPersonAPIClient().destroy_educational_experience_continuing_education_admission(
            uuid=uuid,
            experience_id=experience_id,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_curriculum(cls, person, data, uuid):
        return AdmissionPersonAPIClient().update_continuing_education_completer_curriculum_command_admission(
            uuid=uuid,
            continuing_education_completer_curriculum_command=data,
            **build_mandatory_auth_headers(person),
        )
