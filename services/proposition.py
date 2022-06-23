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
from base.models.person import Person
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.confirmation_paper_canvas import ConfirmationPaperCanvas
from osis_admission_sdk.model.confirmation_paper_dto import ConfirmationPaperDTO
from osis_admission_sdk.model.cotutelle_dto import CotutelleDTO
from osis_admission_sdk.model.doctorate_dto import DoctorateDTO
from osis_admission_sdk.model.doctorate_identity_dto import DoctorateIdentityDTO
from osis_admission_sdk.model.proposition_dto import PropositionDTO
from osis_admission_sdk.model.supervision_dto import SupervisionDTO


class AdmissionPropositionAPIClient:
    def __new__(cls):
        api_config = admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class AdmissionPropositionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_dashboard_links(cls, person: Person):
        return (
            AdmissionPropositionAPIClient()
            .retrieve_dashboard(**build_mandatory_auth_headers(person))
            .to_dict()
            .get('links', {})
        )

    @classmethod
    def create_proposition(cls, person: Person, **kwargs):
        return AdmissionPropositionAPIClient().create_proposition(
            initier_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
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
    def get_supervised_propositions(cls, person: Person):
        return AdmissionPropositionAPIClient().list_supervised_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def cancel_proposition(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().destroy_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def request_signatures(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().create_signatures(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def verify_proposition(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().verify_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_proposition(cls, person: Person, uuid):
        return AdmissionPropositionAPIClient().submit_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )


class PropositionBusinessException(Enum):
    MaximumPropositionsAtteintException = "PROPOSITION-1"
    DoctoratNonTrouveException = "PROPOSITION-2"
    PropositionNonTrouveeException = "PROPOSITION-3"
    GroupeDeSupervisionNonTrouveException = "PROPOSITION-4"
    ProximityCommissionInconsistantException = "PROPOSITION-5"
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
    CandidatNonTrouveException = "PROPOSITION-24"
    IdentificationNonCompleteeException = "PROPOSITION-25"
    NumeroIdentiteNonSpecifieException = "PROPOSITION-26"
    NumeroIdentiteBelgeNonSpecifieException = "PROPOSITION-27"
    DateOuAnneeNaissanceNonSpecifieeException = "PROPOSITION-28"
    DetailsPasseportNonSpecifiesException = "PROPOSITION-29"
    CarteIdentiteeNonSpecifieeException = "PROPOSITION-30"
    AdresseDomicileLegalNonCompleteeException = "PROPOSITION-31"
    AdresseCorrespondanceNonCompleteeException = "PROPOSITION-32"
    LanguesConnuesNonSpecifieesException = "PROPOSITION-33"
    FichierCurriculumNonRenseigneException = "PROPOSITION-34"
    AnneesCurriculumNonSpecifieesException = "PROPOSITION-35"
    ProcedureDemandeSignatureNonLanceeException = "PROPOSITION-36"
    PropositionNonApprouveeParPromoteurException = "PROPOSITION-37"
    PropositionNonApprouveeParMembresCAException = "PROPOSITION-38"
    InstitutTheseObligatoireException = "PROPOSITION-39"
    NomEtPrenomNonSpecifiesException = "PROPOSITION-40"
    SpecifierNOMASiDejaInscritException = "PROPOSITION-41"


BUSINESS_EXCEPTIONS_BY_TAB = {
    'person': {
        PropositionBusinessException.IdentificationNonCompleteeException,
        PropositionBusinessException.NumeroIdentiteNonSpecifieException,
        PropositionBusinessException.NumeroIdentiteBelgeNonSpecifieException,
        PropositionBusinessException.DateOuAnneeNaissanceNonSpecifieeException,
        PropositionBusinessException.DetailsPasseportNonSpecifiesException,
        PropositionBusinessException.CarteIdentiteeNonSpecifieeException,
        PropositionBusinessException.NomEtPrenomNonSpecifiesException,
        PropositionBusinessException.SpecifierNOMASiDejaInscritException,
    },
    'coordonnees': {
        PropositionBusinessException.AdresseDomicileLegalNonCompleteeException,
        PropositionBusinessException.AdresseCorrespondanceNonCompleteeException,
    },
    'education': set(),
    'curriculum': {
        PropositionBusinessException.FichierCurriculumNonRenseigneException,
        PropositionBusinessException.AnneesCurriculumNonSpecifieesException,
    },
    'languages': {
        PropositionBusinessException.LanguesConnuesNonSpecifieesException,
    },
    'project': {
        PropositionBusinessException.DetailProjetNonCompleteException,
    },
    'cotutelle': {
        PropositionBusinessException.CotutelleNonCompleteException,
    },
    'supervision': {
        PropositionBusinessException.ProcedureDemandeSignatureNonLanceeException,
        PropositionBusinessException.PropositionNonApprouveeParPromoteurException,
        PropositionBusinessException.PropositionNonApprouveeParMembresCAException,
    },
    'confirm': set(),
    'confirmation-paper': set(),
    'extension-request': set(),
}

TAB_OF_BUSINESS_EXCEPTION = {}
for tab in BUSINESS_EXCEPTIONS_BY_TAB:
    for exception in BUSINESS_EXCEPTIONS_BY_TAB[tab]:
        TAB_OF_BUSINESS_EXCEPTION[exception.value] = tab


class AdmissionCotutelleService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
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


class AdmissionSupervisionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_supervision(cls, person, uuid) -> SupervisionDTO:
        return AdmissionPropositionAPIClient().retrieve_supervision(uuid=uuid, **build_mandatory_auth_headers(person))

    @classmethod
    def get_signature_conditions(cls, person, uuid) -> SupervisionDTO:
        return AdmissionPropositionAPIClient().retrieve_verify_project(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def add_member(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().add_member(
            uuid=uuid,
            supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_member(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().remove_member(
            uuid=uuid,
            supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_proposition(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().approve_proposition(
            uuid=uuid,
            approuver_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def reject_proposition(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().reject_proposition(
            uuid=uuid,
            refuser_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_by_pdf(cls, person, uuid, **kwargs):
        return AdmissionPropositionAPIClient().approve_by_pdf(
            uuid=uuid,
            approuver_proposition_par_pdf_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class AdmissionDoctorateService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_doctorate(cls, person, uuid) -> DoctorateDTO:
        return AdmissionPropositionAPIClient().retrieve_doctorate_dto(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_confirmation_papers(cls, person, uuid) -> List[ConfirmationPaperDTO]:
        return AdmissionPropositionAPIClient().retrieve_confirmation_papers(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper(cls, person, uuid) -> ConfirmationPaperDTO:
        return AdmissionPropositionAPIClient().retrieve_last_confirmation_paper(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_last_confirmation_paper_canvas(cls, person, uuid) -> ConfirmationPaperCanvas:
        return AdmissionPropositionAPIClient().retrieve_last_confirmation_paper_canvas(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return AdmissionPropositionAPIClient().submit_confirmation_paper(
            uuid=uuid,
            submit_confirmation_paper_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def complete_confirmation_paper_by_promoter(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return AdmissionPropositionAPIClient().complete_confirmation_paper_by_promoter(
            uuid=uuid,
            complete_confirmation_paper_by_promoter_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_confirmation_paper_extension_request(cls, person, uuid, **kwargs) -> DoctorateIdentityDTO:
        return AdmissionPropositionAPIClient().submit_confirmation_paper_extension_request(
            uuid=uuid,
            submit_confirmation_paper_extension_request_command=kwargs,
            **build_mandatory_auth_headers(person),
        )
