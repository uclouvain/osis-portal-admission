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
from enum import Enum

from base.models.person import Person
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import api_exception_handler, build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.cotutelle_dto import CotutelleDTO
from osis_admission_sdk.model.proposition_dto import PropositionDTO
from osis_admission_sdk.model.supervision_dto import SupervisionDTO


class AdmissionPropositionAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class AdmissionPropositionService:
    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def create_proposition(cls, person: Person, **kwargs):
        return AdmissionPropositionAPIClient().create_proposition(
            initier_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def update_proposition(cls, person: Person, **kwargs):
        return AdmissionPropositionAPIClient().update_proposition(
            uuid=kwargs['uuid'],
            completer_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_proposition(cls, person: Person, uuid) -> PropositionDTO:
        return AdmissionPropositionAPIClient().retrieve_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_propositions(cls, person: Person):
        return AdmissionPropositionAPIClient().list_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def cancel_proposition(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().destroy_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def request_signatures(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().create_signatures(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def verify_proposition(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().retrieve_verify_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )


class PropositionBusinessException(Enum):
    MaximumPropositionsAtteintException = "PROPOSITION-1"
    DoctoratNonTrouveException = "PROPOSITION-2"
    PropositionNonTrouveeException = "PROPOSITION-3"
    GroupeDeSupervisionNonTrouveException = "PROPOSITION-4"
    ProximityCommissionCDEInconsistantException = "PROPOSITION-5"
    ContratTravailInconsistantException = "PROPOSITION-6"
    InstitutionInconsistanteException = "PROPOSITION-7"
    MembreGroupeDeSupervisionNonTrouveException = "PROPOSITION-8"
    PromoteurNonTrouveException = "PROPOSITION-9"
    MembreCANonTrouveException = "PROPOSITION-10"
    SignataireNonTrouveException = "PROPOSITION-11"
    SignataireDejaInviteException = "PROPOSITION-12"
    SignatairePasInviteException = "PROPOSITION-13"
    DejaPromoteurException = "PROPOSITION-14"
    DejaMembreCAException = "PROPOSITION-15"
    JustificationRequiseException = "PROPOSITION-16"
    DetailProjetNonCompleteException = "PROPOSITION-17"
    CotutelleNonCompleteException = "PROPOSITION-18"
    PromoteurManquantException = "PROPOSITION-19"
    MembreCAManquantException = "PROPOSITION-20"
    CotutelleDoitAvoirAuMoinsUnPromoteurExterneException = "PROPOSITION-21"
    GroupeSupervisionCompletPourPromoteursException = "PROPOSITION-22"
    GroupeSupervisionCompletPourMembresCAException = "PROPOSITION-23"
    ProximityCommissionCDSSInconsistantException = "PROPOSITION-24"


class AdmissionCotutelleService:
    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def update_cotutelle(cls, person, **kwargs):
        uuid = str(kwargs.pop('uuid'))
        return AdmissionPropositionAPIClient().update_cotutelle(
            uuid=uuid,
            definir_cotutelle_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_cotutelle(cls, person, uuid) -> CotutelleDTO:
        return AdmissionPropositionAPIClient().retrieve_cotutelle(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )


class AdmissionSupervisionService:
    @classmethod
    def get_supervision(cls, person, uuid) -> SupervisionDTO:
        return AdmissionPropositionAPIClient().retrieve_supervision(uuid=uuid, **build_mandatory_auth_headers(person))

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def add_member(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().add_member(
            uuid=uuid,
            supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    @api_exception_handler(api_exception_cls=ApiException)
    def remove_member(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().remove_member(
            uuid=uuid,
            supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )
