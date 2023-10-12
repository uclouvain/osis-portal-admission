# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from enum import Enum
from typing import List

import osis_admission_sdk
from django.conf import settings
from django.utils.translation import get_language
from osis_admission_sdk import ApiClient, ApiException
from osis_admission_sdk.api import propositions_api
from osis_admission_sdk.model.continuing_education_proposition_dto import ContinuingEducationPropositionDTO
from osis_admission_sdk.model.cotutelle_dto import CotutelleDTO
from osis_admission_sdk.model.doctorate_education_accounting_dto import DoctorateEducationAccountingDTO
from osis_admission_sdk.model.doctorate_proposition_dto import DoctoratePropositionDTO
from osis_admission_sdk.model.general_education_accounting_dto import GeneralEducationAccountingDTO
from osis_admission_sdk.model.general_education_proposition_dto import GeneralEducationPropositionDTO
from osis_admission_sdk.model.jury_identity_dto import JuryIdentityDTO
from osis_admission_sdk.model.membre_jury_identity_dto import MembreJuryIdentityDTO
from osis_admission_sdk.model.specific_question import SpecificQuestion
from osis_admission_sdk.model.supervision_dto import SupervisionDTO

from admission.services.mixins import ServiceMeta
from base.models.person import Person
from frontoffice.settings.osis_sdk import admission as admission_sdk
from frontoffice.settings.osis_sdk.utils import build_mandatory_auth_headers

__all__ = [
    "AdmissionPropositionService",
    "AdmissionCotutelleService",
    "AdmissionSupervisionService",
    "TAB_OF_BUSINESS_EXCEPTION",
    "BUSINESS_EXCEPTIONS_BY_TAB",
    "PropositionBusinessException",
]


class APIClient:
    def __new__(cls, api_config=None):
        api_config = api_config or admission_sdk.build_configuration()
        return propositions_api.PropositionsApi(ApiClient(configuration=api_config))


class AdmissionPropositionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def get_dashboard_links(cls, person: Person):
        return APIClient().retrieve_dashboard(**build_mandatory_auth_headers(person)).to_dict().get('links', {})

    @classmethod
    def list_proposition_create_permissions(cls, person):
        return APIClient().detail_proposition_create_permissions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_doctorate_proposition(cls, person: Person, data):
        return APIClient().create_doctorate_training_choice(
            initier_proposition_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_general_identification(cls, person: Person, uuid_proposition: str):
        return APIClient().retrieve_general_identification(
            uuid=uuid_proposition,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_general_education_proposition(cls, person: Person, data):
        return APIClient().create_general_training_choice(
            initier_proposition_generale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_continuing_education_proposition(cls, person: Person, data):
        return APIClient().create_continuing_training_choice(
            initier_proposition_continue_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_general_education_choice(cls, person: Person, uuid, data):
        return APIClient().update_general_training_choice(
            uuid=uuid,
            modifier_choix_formation_generale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_continuing_education_choice(cls, person: Person, uuid, data):
        return APIClient().update_continuing_training_choice(
            uuid=uuid,
            modifier_choix_formation_continue_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_doctorate_education_choice(cls, person: Person, uuid, data):
        return APIClient().update_doctorate_training_choice(
            uuid=uuid,
            modifier_type_admission_doctorale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_proposition(cls, person: Person, **kwargs):
        return APIClient().update_proposition(
            uuid=kwargs['uuid'],
            completer_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_proposition(cls, person: Person, uuid) -> DoctoratePropositionDTO:
        return APIClient().retrieve_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_general_education_proposition(cls, person: Person, uuid) -> GeneralEducationPropositionDTO:
        return APIClient().retrieve_general_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_general_education_training_choice(cls, person: Person, uuid) -> None:
        return APIClient().list_general_training_choices(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_continuing_education_proposition(cls, person: Person, uuid) -> ContinuingEducationPropositionDTO:
        return APIClient().retrieve_continuing_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_continuing_education_training_choice(cls, person: Person, uuid) -> None:
        return APIClient().list_continuing_training_choices(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def cancel_general_education_proposition(cls, person: Person, uuid):
        return APIClient().destroy_general_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def cancel_continuing_education_proposition(cls, person: Person, uuid):
        return APIClient().destroy_continuing_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_propositions(cls, person: Person):
        return APIClient().list_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_supervised_propositions(cls, person: Person):
        return APIClient().list_supervised_propositions(
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def cancel_proposition(cls, person: Person, uuid):
        return APIClient().destroy_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def request_signatures(cls, person: Person, uuid):
        return APIClient().create_signatures(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def verify_proposition(cls, person: Person, uuid):
        return APIClient().verify_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_proposition(cls, person: Person, uuid, **kwargs):
        return APIClient().submit_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
            submit_proposition=kwargs,
        )

    @classmethod
    def verify_general_proposition(cls, person: Person, uuid):
        return APIClient().verify_general_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_general_proposition(cls, person: Person, uuid, **kwargs):
        return APIClient().submit_general_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
            submit_proposition=kwargs,
        )

    @classmethod
    def verify_continuing_proposition(cls, person: Person, uuid):
        return APIClient().verify_continuing_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def submit_continuing_proposition(cls, person: Person, uuid, **kwargs):
        return APIClient().submit_continuing_education_proposition(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
            submit_proposition=kwargs,
        )

    @classmethod
    def retrieve_doctorate_accounting(cls, person: Person, uuid: str) -> DoctorateEducationAccountingDTO:
        return APIClient().retrieve_accounting(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_general_accounting(cls, person: Person, uuid: str) -> GeneralEducationAccountingDTO:
        return APIClient().retrieve_general_accounting(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_doctorate_accounting(cls, person: Person, uuid: str, data: dict):
        data['uuid_proposition'] = uuid
        return APIClient().update_accounting(
            uuid=uuid,
            completer_comptabilite_proposition_doctorale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_general_accounting(cls, person: Person, uuid: str, data: dict):
        data['uuid_proposition'] = uuid
        return APIClient().update_general_accounting(
            uuid=uuid,
            completer_comptabilite_proposition_generale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_doctorate_specific_questions(cls, person: Person, uuid: str, tab_name: str) -> List[SpecificQuestion]:
        return APIClient().list_doctorate_specific_questions(
            uuid=uuid,
            tab=tab_name,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_general_specific_questions(cls, person: Person, uuid: str, tab_name: str) -> List[SpecificQuestion]:
        return APIClient().list_general_specific_questions(
            uuid=uuid,
            tab=tab_name,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_continuing_specific_questions(cls, person: Person, uuid: str, tab_name: str) -> List[SpecificQuestion]:
        return APIClient().list_continuing_specific_questions(
            uuid=uuid,
            tab=tab_name,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_general_specific_question(cls, person: Person, uuid: str, data: dict):
        return APIClient().update_general_specific_question(
            uuid=uuid,
            modifier_questions_specifiques_formation_generale_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_continuing_specific_question(cls, person: Person, uuid: str, data: dict):
        return APIClient().update_continuing_specific_question(
            uuid=uuid,
            modifier_questions_specifiques_formation_continue_command=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_pool_questions(cls, person: Person, uuid: str):
        return APIClient().retrieve_pool_questions(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_pool_questions(cls, person: Person, uuid: str, data: dict):
        return APIClient().update_pool_questions(
            uuid=uuid,
            pool_questions=data,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_general_education_pdf_recap(cls, person: Person, uuid):
        return APIClient().retrieve_general_education_proposition_pdf_recap(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_continuing_education_pdf_recap(cls, person: Person, uuid):
        return APIClient().retrieve_continuing_education_proposition_pdf_recap(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_doctorate_education_pdf_recap(cls, person: Person, uuid):
        return APIClient().retrieve_doctorate_education_proposition_pdf_recap(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_general_education_documents(cls, person: Person, uuid):
        return APIClient().list_general_documents(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_general_education_documents(cls, person: Person, data, uuid):
        return APIClient().create_general_documents(
            completer_emplacements_documents_par_candidat_command=data,
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def open_application_fees_payment_after_submission(cls, person: Person, uuid):
        return APIClient().open_application_fees_payment_after_submission(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def open_application_fees_payment_after_request(cls, person: Person, uuid):
        return APIClient().open_application_fees_payment_after_request(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_application_fees_payments(cls, person: Person, uuid):
        return APIClient().list_application_fees_payments(
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
    DomaineTheseInconsistantException = "PROPOSITION-8"
    PromoteurNonTrouveException = "PROPOSITION-9"
    MembreCANonTrouveException = "PROPOSITION-10"
    SignataireNonTrouveException = "PROPOSITION-11"
    SignataireDejaInviteException = "PROPOSITION-12"
    SignatairePasInviteException = "PROPOSITION-13"
    MembreSoitInterneSoitExterneException = "PROPOSITION-14"
    DejaMembreException = "PROPOSITION-15"
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
    PromoteurDeReferenceManquantException = "PROPOSITION-42"
    AbsenceDeDetteNonCompleteeException = "PROPOSITION-43"
    ReductionDesDroitsInscriptionNonCompleteeException = "PROPOSITION-44"
    AssimilationNonCompleteeException = "PROPOSITION-45"
    AffiliationsNonCompleteesException = "PROPOSITION-46"
    CarteBancaireRemboursementIbanNonCompleteException = "PROPOSITION-47"
    CarteBancaireRemboursementAutreFormatNonCompleteException = "PROPOSITION-48"
    ExperiencesAcademiquesNonCompleteesException = "PROPOSITION-49"
    TypeCompteBancaireRemboursementNonCompleteException = "PROPOSITION-50"
    CoordonneesNonCompleteesException = "PROPOSITION-51"


class PostalCodeBusinessException(Enum):
    PersonResidentialAddressBadPostalCodeFormatException = "RESIDENTIAL-PERSON-ADDRESS-1"
    PersonContactAddressBadPostalCodeFormatException = "CONTACT-PERSON-ADDRESS-1"


class BelgianNissBusinessException(Enum):
    BelgianNISSCharactersException = "BELGIAN-NISS-1"
    BelgianNISSLengthException = "BELGIAN-NISS-2"
    BelgianNISSBirthDateException = "BELGIAN-NISS-3"
    BelgianNISSSexException = "BELGIAN-NISS-4"
    BelgianNISSChecksumException = "BELGIAN-NISS-5"
    BelgianMissingBirthDataException = "BELGIAN-NISS-6"


class GlobalPropositionBusinessException(Enum):
    BourseNonTrouveeException = "ADMISSION-1"
    ConditionsAccessNonRempliesException = "ADMISSION-2"
    QuestionsSpecifiquesChoixFormationNonCompleteesException = "ADMISSION-3"
    QuestionsSpecifiquesCurriculumNonCompleteesException = "ADMISSION-4"
    QuestionsSpecifiquesEtudesSecondairesNonCompleteesException = "ADMISSION-5"
    QuestionsSpecifiquesInformationsComplementairesNonCompleteesException = "ADMISSION-6"
    FormationNonTrouveeException = "ADMISSION-7"
    ReorientationInscriptionExterneNonConfirmeeException = "ADMISSION-8"
    ModificationInscriptionExterneNonConfirmeeException = "ADMISSION-9"
    PoolNonResidentContingenteNonOuvertException = "ADMISSION-10"
    ResidenceAuSensDuDecretNonRenseigneeException = "ADMISSION-11"
    AucunPoolCorrespondantException = "ADMISSION-12"
    PoolOuAnneeDifferentException = "ADMISSION-13"
    ElementsConfirmationNonConcordants = "ADMISSION-14"
    NombrePropositionsSoumisesDepasseException = "ADMISSION-15"


class FormationGeneraleBusinessException(Enum):
    FormationNonTrouveeException = "FORMATION-GENERALE-1"
    PropositionNonTrouveeException = "FORMATION-GENERALE-2"
    EtudesSecondairesNonCompleteesException = "FORMATION-GENERALE-3"
    FichierCurriculumNonRenseigneException = "FORMATION-GENERALE-4"
    EquivalenceNonRenseigneeException = "FORMATION-GENERALE-5"
    EtudesSecondairesNonCompleteesPourDiplomeBelgeException = "FORMATION-GENERALE-8"
    EtudesSecondairesNonCompleteesPourDiplomeEtrangerException = "FORMATION-GENERALE-9"
    EtudesSecondairesNonCompleteesPourAlternativeException = "FORMATION-GENERALE-10"
    PropositionPourPaiementInvalideException = "FORMATION-GENERALE-11"
    PropositionDoitEtreEnAttenteDePaiementException = "FORMATION-GENERALE-12"
    StatutPropositionInvalidePourPaiementInscriptionException = "FORMATION-GENERALE-13"
    PaiementNonRealiseException = "FORMATION-GENERALE-14"
    SituationPropositionNonSICException = "FORMATION-GENERALE-15"
    SituationPropositionNonFACException = "FORMATION-GENERALE-16"
    MotifRefusFacultaireNonSpecifieException = "FORMATION-GENERALE-17"
    InformationsAcceptationFacultaireNonSpecifieesException = "FORMATION-GENERALE-18"
    PaiementDejaRealiseException = "FORMATION-GENERALE-19"
    InformationsVisaNonCompleteesException = "FORMATION-GENERALE-20"


class FormationContinueBusinessException(Enum):
    ExperiencesCurriculumNonRenseigneesException = "FORMATION-CONTINUE-3"
    InformationsComplementairesNonRenseigneesException = "FORMATION-CONTINUE-4"


class JuryBusinessException(Enum):
    PromoteurPresidentException = "JURY-1"
    MembreNonTrouveDansJuryException = "JURY-3"
    JuryNonTrouveException = "JURY-4"
    PromoteurRetireException = "JURY-5"
    PromoteurModifieException = "JURY-6"
    NonDocteurSansJustificationException = "JURY-7"
    MembreExterneSansInstitutionException = "JURY-8"
    MembreExterneSansPaysException = "JURY-9"
    MembreExterneSansNomException = "JURY-10"
    MembreExterneSansPrenomException = "JURY-11"
    MembreExterneSansTitreException = "JURY-12"
    MembreExterneSansGenreException = "JURY-13"
    MembreExterneSansEmailException = "JURY-14"
    MembreDejaDansJuryException = "JURY-15"


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
        BelgianNissBusinessException.BelgianNISSCharactersException,
        BelgianNissBusinessException.BelgianNISSLengthException,
        BelgianNissBusinessException.BelgianNISSBirthDateException,
        BelgianNissBusinessException.BelgianNISSSexException,
        BelgianNissBusinessException.BelgianNISSChecksumException,
        BelgianNissBusinessException.BelgianMissingBirthDataException,
    },
    'coordonnees': {
        PropositionBusinessException.AdresseDomicileLegalNonCompleteeException,
        PropositionBusinessException.AdresseCorrespondanceNonCompleteeException,
        PropositionBusinessException.CoordonneesNonCompleteesException,
        PostalCodeBusinessException.PersonResidentialAddressBadPostalCodeFormatException,
        PostalCodeBusinessException.PersonContactAddressBadPostalCodeFormatException,
    },
    'education': {
        GlobalPropositionBusinessException.QuestionsSpecifiquesEtudesSecondairesNonCompleteesException,
        FormationGeneraleBusinessException.EtudesSecondairesNonCompleteesException,
        FormationGeneraleBusinessException.EtudesSecondairesNonCompleteesPourDiplomeBelgeException,
        FormationGeneraleBusinessException.EtudesSecondairesNonCompleteesPourDiplomeEtrangerException,
        FormationGeneraleBusinessException.EtudesSecondairesNonCompleteesPourAlternativeException,
    },
    'curriculum': {
        PropositionBusinessException.FichierCurriculumNonRenseigneException,
        PropositionBusinessException.AnneesCurriculumNonSpecifieesException,
        PropositionBusinessException.ExperiencesAcademiquesNonCompleteesException,
        GlobalPropositionBusinessException.QuestionsSpecifiquesCurriculumNonCompleteesException,
        FormationGeneraleBusinessException.FichierCurriculumNonRenseigneException,
        FormationGeneraleBusinessException.FormationNonTrouveeException,
        FormationGeneraleBusinessException.EquivalenceNonRenseigneeException,
        FormationContinueBusinessException.ExperiencesCurriculumNonRenseigneesException,
    },
    'languages': {
        PropositionBusinessException.LanguesConnuesNonSpecifieesException,
    },
    'project': {
        PropositionBusinessException.DetailProjetNonCompleteException,
    },
    'training-choice': {
        GlobalPropositionBusinessException.QuestionsSpecifiquesChoixFormationNonCompleteesException,
        GlobalPropositionBusinessException.BourseNonTrouveeException,
        GlobalPropositionBusinessException.FormationNonTrouveeException,
    },
    'cotutelle': {
        PropositionBusinessException.CotutelleNonCompleteException,
    },
    'supervision': {
        PropositionBusinessException.ProcedureDemandeSignatureNonLanceeException,
        PropositionBusinessException.PropositionNonApprouveeParPromoteurException,
        PropositionBusinessException.PropositionNonApprouveeParMembresCAException,
        PropositionBusinessException.PromoteurManquantException,
        PropositionBusinessException.PromoteurDeReferenceManquantException,
        PropositionBusinessException.MembreCAManquantException,
        PropositionBusinessException.CotutelleDoitAvoirAuMoinsUnPromoteurExterneException,
    },
    'confirm-submit': {
        GlobalPropositionBusinessException.ConditionsAccessNonRempliesException,
        GlobalPropositionBusinessException.PoolNonResidentContingenteNonOuvertException,
        GlobalPropositionBusinessException.AucunPoolCorrespondantException,
        GlobalPropositionBusinessException.NombrePropositionsSoumisesDepasseException,
    },
    'confirmation-paper': set(),
    'extension-request': set(),
    'doctoral-training': set(),
    'complementary-training': set(),
    'course-enrollment': set(),
    'accounting': {
        PropositionBusinessException.AbsenceDeDetteNonCompleteeException,
        PropositionBusinessException.ReductionDesDroitsInscriptionNonCompleteeException,
        PropositionBusinessException.AssimilationNonCompleteeException,
        PropositionBusinessException.AffiliationsNonCompleteesException,
        PropositionBusinessException.CarteBancaireRemboursementIbanNonCompleteException,
        PropositionBusinessException.CarteBancaireRemboursementAutreFormatNonCompleteException,
        PropositionBusinessException.TypeCompteBancaireRemboursementNonCompleteException,
    },
    'specific-questions': {
        GlobalPropositionBusinessException.QuestionsSpecifiquesInformationsComplementairesNonCompleteesException,
        GlobalPropositionBusinessException.ReorientationInscriptionExterneNonConfirmeeException,
        GlobalPropositionBusinessException.ModificationInscriptionExterneNonConfirmeeException,
        GlobalPropositionBusinessException.ResidenceAuSensDuDecretNonRenseigneeException,
        FormationContinueBusinessException.InformationsComplementairesNonRenseigneesException,
        FormationGeneraleBusinessException.InformationsVisaNonCompleteesException,
    },
    'documents': set(),
    'jury-preparation': set(),
    'jury': set(),
    'payment': set(),
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
        return APIClient().update_cotutelle(
            uuid=uuid,
            definir_cotutelle_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def get_cotutelle(cls, person, uuid) -> CotutelleDTO:
        return APIClient().retrieve_cotutelle(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )


class AdmissionSupervisionService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_admission_sdk.Configuration(
            host=settings.OSIS_ADMISSION_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.ADMISSION_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def get_supervision(cls, person, uuid) -> SupervisionDTO:
        return APIClient().retrieve_supervision(uuid=uuid, **build_mandatory_auth_headers(person))

    @classmethod
    def get_external_supervision(cls, uuid, token):
        return APIClient(api_config=cls.build_config()).get_external_proposition(
            uuid=uuid,
            token=token,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def get_signature_conditions(cls, person, uuid) -> SupervisionDTO:
        return APIClient().retrieve_verify_project(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def add_member(cls, person, uuid, **kwargs):
        return APIClient().add_member(
            uuid=uuid,
            identifier_supervision_actor=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def edit_external_member(cls, person, uuid, **kwargs):
        return APIClient().edit_external_member(
            uuid=uuid,
            modifier_membre_supervision_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_member(cls, person, uuid, **kwargs):
        return APIClient().remove_member(
            uuid=uuid,
            supervision_actor_reference=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def set_reference_promoter(cls, person, uuid, **kwargs):
        return APIClient().set_reference_promoter(
            uuid=uuid,
            designer_promoteur_reference_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def resend_invite(cls, person, uuid, **kwargs):
        return APIClient().update_signatures(
            uuid=uuid,
            renvoyer_invitation_signature_externe=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_proposition(cls, person, uuid, **kwargs):
        return APIClient().approve_proposition(
            uuid=uuid,
            approuver_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def reject_proposition(cls, person, uuid, **kwargs):
        return APIClient().reject_proposition(
            uuid=uuid,
            refuser_proposition_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def approve_external_proposition(cls, uuid, token, **kwargs):
        return APIClient(api_config=cls.build_config()).approve_external_proposition(
            uuid=uuid,
            token=token,
            approuver_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def reject_external_proposition(cls, uuid, token, **kwargs):
        return APIClient(api_config=cls.build_config()).reject_external_proposition(
            uuid=uuid,
            token=token,
            refuser_proposition_command=kwargs,
            **cls.build_mandatory_external_headers(),
        )

    @classmethod
    def approve_by_pdf(cls, person, uuid, **kwargs):
        return APIClient().approve_by_pdf(
            uuid=uuid,
            approuver_proposition_par_pdf_command=kwargs,
            **build_mandatory_auth_headers(person),
        )


class AdmissionJuryService(metaclass=ServiceMeta):
    api_exception_cls = ApiException

    @classmethod
    def build_config(cls):
        return osis_admission_sdk.Configuration(
            host=settings.OSIS_ADMISSION_SDK_HOST,
            api_key_prefix={'Token': 'Token'},
            api_key={'Token': settings.ADMISSION_TOKEN_EXTERNAL},
        )

    @staticmethod
    def build_mandatory_external_headers():
        return {
            'accept_language': get_language(),
        }

    @classmethod
    def retrieve_jury(cls, person, uuid, **kwargs) -> JuryIdentityDTO:
        return APIClient().retrieve_jury_preparation(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def modifier_jury(cls, person, uuid, **kwargs) -> JuryIdentityDTO:
        return APIClient().update_jury_preparation(
            uuid=uuid,
            modifier_jury_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def list_jury_members(cls, person, uuid, **kwargs) -> List[MembreJuryIdentityDTO]:
        return APIClient().list_jury_members(
            uuid=uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def create_jury_member(cls, person, uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().create_jury_members(
            uuid=uuid,
            ajouter_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def retrieve_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().retrieve_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def remove_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().remove_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().update_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            modifier_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )

    @classmethod
    def update_role_jury_member(cls, person, uuid, member_uuid, **kwargs) -> MembreJuryIdentityDTO:
        return APIClient().update_role_jury_member(
            uuid=uuid,
            member_uuid=member_uuid,
            modifier_role_membre_command=kwargs,
            **build_mandatory_auth_headers(person),
        )
