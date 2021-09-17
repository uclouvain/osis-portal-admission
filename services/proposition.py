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
from frontoffice.settings.osis_sdk.utils import api_exception_handler
from osis_admission_sdk import ApiClient, ApiException

from frontoffice.settings.osis_sdk import admission as admission_sdk
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.proposition_dto import PropositionDTO


class AdmissionPropositionAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class AdmissionPropositionService:
    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def create_proposition(cls, **kwargs):
        return AdmissionPropositionAPIClient().create_proposition(initier_proposition_command=kwargs)

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def update_proposition(cls, **kwargs):
        return AdmissionPropositionAPIClient().update_proposition(
            uuid=kwargs['uuid'],
            completer_proposition_command=kwargs,
        )

    @classmethod
    def get_proposition(cls, uuid) -> PropositionDTO:
        return AdmissionPropositionAPIClient().retrieve_proposition(uuid=uuid)

    @classmethod
    def get_propositions(cls):
        return AdmissionPropositionAPIClient().list_propositions()
