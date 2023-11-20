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
from enum import Enum
from typing import List

from admission.services.mixins import ServiceMeta
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.confirmation_paper_canvas import ConfirmationPaperCanvas
from osis_admission_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO
from osis_admission_sdk.model.doctorate_dto import DoctorateDTO
from osis_admission_sdk.model.doctorate_identity_dto import DoctorateIdentityDTO
from frontoffice.settings.osis_sdk import admission as admission_sdk


class APIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class AdmissionDoctorateService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_doctorate(cls, person, uuid) -> DoctorateDTO:
        return APIClient().retrieve_doctorate_dto(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_confirmation_papers(cls, person, uuid) -> List[ConfirmationPaperDTO]:
        return APIClient().retrieve_confirmation_papers(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper(cls, person, uuid) -> ConfirmationPaperDTO:
        return APIClient().retrieve_last_confirmation_paper(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper_canvas(cls, person, uuid) -> ConfirmationPaperCanvas:
        return APIClient().retrieve_last_confirmation_paper_canvas(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().submit_confirmation_paper(
            uuid=uuid,
            submit_confirmation_paper_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def complete_confirmation_paper_by_promoter(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().complete_confirmation_paper_by_promoter(
            uuid=uuid,
            complete_confirmation_paper_by_promoter_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper_extension_request(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return APIClient().submit_confirmation_paper_extension_request(
            uuid=uuid,
            submit_confirmation_paper_extension_request_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class ConfirmationPaperBusinessException(Enum):
    EpreuveConfirmationNonTrouveeException = "EPREUVE-CONFIRMATION-1"
    EpreuveConfirmationNonCompleteeException = "EPREUVE-CONFIRMATION-2"
    EpreuveConfirmationDateIncorrecteException = "EPREUVE-CONFIRMATION-3"
    DemandeProlongationNonCompleteeException = "EPREUVE-CONFIRMATION-4"
    AvisProlongationNonCompleteException = "EPREUVE-CONFIRMATION-5"
    DemandeProlongationNonDefinieException = "EPREUVE-CONFIRMATION-6"
    EpreuveConfirmationNonCompleteePourEvaluationException = "EPREUVE-CONFIRMATION-7"
