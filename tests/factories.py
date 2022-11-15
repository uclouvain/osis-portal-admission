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
import factory

from admission.contrib.enums import (
    TypeSituationAssimilation,
    ChoixAffiliationSport,
    ChoixTypeCompteBancaire,
    LienParente,
)
from osis_admission_sdk.model.doctorate_proposition_dto_comptabilite import DoctoratePropositionDTOComptabilite


class PropositionDTOComptabiliteFactory(factory.Factory):
    class Meta:
        model = DoctoratePropositionDTOComptabilite
        abstract = False

    demande_allocation_d_etudes_communaute_francaise_belgique = False
    enfant_personnel = False
    type_situation_assimilation = TypeSituationAssimilation.AUCUNE_ASSIMILATION.name
    affiliation_sport = ChoixAffiliationSport.NON.name
    etudiant_solidaire = False
    type_numero_compte = ChoixTypeCompteBancaire.NON.name
    relation_parente = LienParente.COHABITANT_LEGAL.name
    attestation_absence_dette_etablissement = []
    attestation_enfant_personnel = []
    carte_resident_longue_duree = []
    carte_cire_sejour_illimite_etranger = []
    carte_sejour_membre_ue = []
    carte_sejour_permanent_membre_ue = []
    carte_a_b_refugie = []
    annexe_25_26_refugies_apatrides = []
    attestation_immatriculation = []
    carte_a_b = []
    decision_protection_subsidiaire = []
    decision_protection_temporaire = []
    titre_sejour_3_mois_professionel = []
    fiches_remuneration = []
    titre_sejour_3_mois_remplacement = []
    preuve_allocations_chomage_pension_indemnite = []
    attestation_cpas = []
    composition_menage_acte_naissance = []
    acte_tutelle = []
    composition_menage_acte_mariage = []
    attestation_cohabitation_legale = []
    carte_identite_parent = []
    titre_sejour_longue_duree_parent = []
    annexe_25_26_refugies_apatrides_decision_protection_parent = []
    titre_sejour_3_mois_parent = []
    fiches_remuneration_parent = []
    attestation_cpas_parent = []
    decision_bourse_cfwb = []
    attestation_boursier = []
    titre_identite_sejour_longue_duree_ue = []
    titre_sejour_belgique = []
