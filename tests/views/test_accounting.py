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
import uuid
from unittest.mock import ANY, MagicMock, Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    ChoixAffiliationSport,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    ChoixAssimilation5,
    ChoixAssimilation6,
    ChoixStatutPropositionFormationContinue,
    ChoixTypeCompteBancaire,
    FORMATTED_RELATIONSHIPS,
    LienParente,
    TrainingType,
    TypeSituationAssimilation,
    dynamic_person_concerned_lowercase,
)
from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.projet import ChoixStatutProposition, ChoixStatutPropositionFormationGenerale
from admission.contrib.forms import PDF_MIME_TYPE
from base.tests.factories.person import PersonFactory
from reference.services.iban_validator import IBANValidatorException, IBANValidatorRequestException


def validate_with_no_service_exception(value):
    raise IBANValidatorRequestException()


def validate_with_invalid_iban_exception(value):
    raise IBANValidatorException('Invalid IBAN')


def validate_ok(value):
    return True


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class DoctorateAccountingViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition = Mock(
            uuid=str(uuid.uuid4()),
            type_admission=AdmissionType.ADMISSION.name,
            reference='22-300001',
            links={'update_accounting': {'url': 'ok'}},
            doctorat=Mock(
                sigle='CS1',
                annee=2020,
                intitule='Doctorate name',
                sigle_entite_gestion="CDSS",
                campus="Mons",
                type=TrainingType.PHD.name,
            ),
            matricule_candidat=cls.person.global_id,
            code_secteur_formation='CS',
            bourse_preuve=[],
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            langue_redaction_these='FR',
            lieu_these='UCL',
            domaine_these='',
            doctorat_deja_realise='',
            fiche_archive_signatures_envoyees=[],
            statut=ChoixStatutProposition.IN_PROGRESS.name,
            erreurs=[],
            curriculum=[],
        )

        cls.accounting = {
            'attestation_absence_dette_etablissement': ['attestation_absence_dette_etablissement.pdf'],
            'type_situation_assimilation': TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            'carte_resident_longue_duree': ['carte_resident_longue_duree.pdf'],
            'carte_cire_sejour_illimite_etranger': ['carte_cire_sejour_illimite_etranger.pdf'],
            'carte_sejour_membre_ue': ['carte_sejour_membre_ue.pdf'],
            'carte_sejour_permanent_membre_ue': ['carte_sejour_permanent_membre_ue.pdf'],
            'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            'carte_a_b_refugie': ['carte_a_b_refugie.pdf'],
            'annexe_25_26_refugies_apatrides': ['annexe_25_26_refugies_apatrides.pdf'],
            'attestation_immatriculation': ['attestation_immatriculation.pdf'],
            'carte_a_b': ['carte_a_b.pdf'],
            'decision_protection_subsidiaire': ['decision_protection_subsidiaire.pdf'],
            'decision_protection_temporaire': ['decision_protection_temporaire.pdf'],
            'sous_type_situation_assimilation_3': (
                ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
            ),
            'titre_sejour_3_mois_professionel': ['titre_sejour_3_mois_professionel.pdf'],
            'fiches_remuneration': ['fiches_remuneration.pdf'],
            'titre_sejour_3_mois_remplacement': ['titre_sejour_3_mois_remplacement.pdf'],
            'preuve_allocations_chomage_pension_indemnite': ['preuve_allocations_chomage_pension_indemnite.pdf'],
            'attestation_cpas': ['attestation_cpas.pdf'],
            'relation_parente': LienParente.MERE.name,
            'sous_type_situation_assimilation_5': ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'composition_menage_acte_naissance': ['composition_menage_acte_naissance.pdf'],
            'acte_tutelle': ['acte_tutelle.pdf'],
            'composition_menage_acte_mariage': ['composition_menage_acte_mariage.pdf'],
            'attestation_cohabitation_legale': ['attestation_cohabitation_legale.pdf'],
            'carte_identite_parent': ['carte_identite_parent.pdf'],
            'titre_sejour_longue_duree_parent': ['titre_sejour_longue_duree_parent.pdf'],
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [
                'annexe_25_26_refugies_apatrides_decision_protection_parent.pdf'
            ],
            'titre_sejour_3_mois_parent': ['titre_sejour_3_mois_parent.pdf'],
            'fiches_remuneration_parent': ['fiches_remuneration_parent.pdf'],
            'attestation_cpas_parent': ['attestation_cpas_parent.pdf'],
            'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            'decision_bourse_cfwb': ['decision_bourse_cfwb.pdf'],
            'attestation_boursier': ['attestation_boursier.pdf'],
            'titre_identite_sejour_longue_duree_ue': ['titre_identite_sejour_longue_duree_ue.pdf'],
            'titre_sejour_belgique': ['titre_sejour_belgique.pdf'],
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            'numero_compte_iban': 'BE87001431855594',
            'iban_valide': True,
            'numero_compte_autre_format': '0123456789',
            'code_bic_swift_banque': 'GEBABEBB',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
            'derniers_etablissements_superieurs_communaute_fr_frequentes': {
                'names': ['Institut de technologie', 'Institut de pharmacologie'],
                'academic_year': 2021,
            },
            'a_nationalite_ue': False,
        }

        cls.detail_url = resolve_url('admission:doctorate:accounting', pk=cls.proposition.uuid)
        cls.update_url = resolve_url('admission:doctorate:update:accounting', pk=cls.proposition.uuid)

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.retrieve_accounting.return_value.to_dict.return_value = self.accounting

        self.addCleanup(propositions_api_patcher.stop)

        # Mock osis document api
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock iban validator
        iban_validator_patcher = patch("admission.contrib.forms.accounting.IBANValidatorService.validate")
        self.mock_iban_validator = iban_validator_patcher.start()
        self.mock_iban_validator.side_effect = validate_ok
        self.addCleanup(iban_validator_patcher.stop)

        self.client.force_login(self.person.user)

    def test_display_accounting_details(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context['admission'], self.proposition)
        self.assertEqual(response.context['accounting'], self.accounting)
        self.assertEqual(response.context['formatted_relationships'], FORMATTED_RELATIONSHIPS)
        self.assertEqual(response.context['dynamic_person_concerned_lowercase'], dynamic_person_concerned_lowercase)

    def test_display_accounting_form(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form class="osis-form"')
        self.assertContains(response, _("Save and continue"))

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context.get('admission'), self.proposition)
        self.assertEqual(response.context.get('accounting'), self.accounting)
        self.assertEqual(response.context.get('relationships'), {elt.name: elt.value for elt in LienParente})
        self.assertEqual(response.context.get('formatted_relationships'), FORMATTED_RELATIONSHIPS)
        form = response.context['form']

        # Check form initialization
        self.assertEqual(
            form.fields['attestation_absence_dette_etablissement'].label,
            "Attestations stipulant l'absence de dettes vis-à-vis des établissements fréquentés durant l'année "
            "académique 2021-2022 : Institut de technologie, Institut de pharmacologie.",
        )
        self.assertTrue(form.fields['attestation_absence_dette_etablissement'].required)
        self.assertTrue(form.fields['type_situation_assimilation'].required)

    def test_post_accounting_form_with_valid_data(self):
        data = {
            'attestation_absence_dette_etablissement_0': ['file.pdf'],
            'etudiant_solidaire': False,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_autre_format': '123456',
            'numero_compte_iban': 'BE87001431855590',
            'code_bic_swift_banque': 'GKCCBEBA',
            'prenom_titulaire_compte': 'Jim',
            'nom_titulaire_compte': 'Foe',
            'type_situation_assimilation': TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'attestation_cpas_0': ['file.pdf'],
        }

        response = self.client.post(self.update_url, data=data)

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls

        self.mock_proposition_api.return_value.update_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_doctorale_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_accounting.call_args[1][
            'completer_comptabilite_proposition_doctorale_command'
        ]

        self.assertEqual(command_args['attestation_absence_dette_etablissement'], ['file.pdf'])
        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.AUTRE_FORMAT.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '123456')
        self.assertEqual(command_args['numero_compte_iban'], '')
        self.assertEqual(command_args['code_bic_swift_banque'], 'GKCCBEBA')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], True)
        self.assertEqual(
            command_args['type_situation_assimilation'],
            TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
        )
        self.assertEqual(command_args['attestation_cpas'], ['file.pdf'])

        # Valid IBAN
        response = self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        self.mock_proposition_api.return_value.update_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_doctorale_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_accounting.call_args[1][
            'completer_comptabilite_proposition_doctorale_command'
        ]

        self.assertEqual(command_args['attestation_absence_dette_etablissement'], ['file.pdf'])
        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.IBAN.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '')
        self.assertEqual(command_args['numero_compte_iban'], 'BE43068999999501')
        self.assertEqual(command_args['code_bic_swift_banque'], '')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], True)

        # The IBAN validator doesn't work
        self.mock_iban_validator.side_effect = validate_with_no_service_exception

        response = self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        self.mock_proposition_api.return_value.update_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_doctorale_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_accounting.call_args[1][
            'completer_comptabilite_proposition_doctorale_command'
        ]

        self.assertEqual(command_args['attestation_absence_dette_etablissement'], ['file.pdf'])
        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.IBAN.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '')
        self.assertEqual(command_args['numero_compte_iban'], 'BE43068999999501')
        self.assertEqual(command_args['code_bic_swift_banque'], '')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], None)

    def test_accounting_form_with_no_data(self):
        response = self.client.post(self.update_url, data={})

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        missing_fields = [
            'attestation_absence_dette_etablissement',
            'type_situation_assimilation',
            'etudiant_solidaire',
            'type_numero_compte',
        ]
        self.assertCountEqual(missing_fields, form.errors.keys())
        for field in missing_fields:
            self.assertFormError(response, 'form', field, FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_no_data_and_previous_highschool(self):
        mock_accounting = self.mock_proposition_api.return_value.retrieve_accounting.return_value.to_dict.return_value
        mock_accounting['derniers_etablissements_superieurs_communaute_fr_frequentes'] = None
        response = self.client.post(self.update_url, data={})

        # Check the form
        form = response.context.get('form')
        self.assertFalse(form.fields['attestation_absence_dette_etablissement'].required)
        self.assertIsNone(form.errors.get('attestation_absence_dette_etablissement'))

    def test_accounting_form_with_incomplete_bank_account_for_iban(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_with_invalid_iban(self):
        # The IBAN is not valid
        self.mock_iban_validator.side_effect = validate_with_invalid_iban_exception

        response = self.client.post(
            self.update_url,
            data={'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name, 'numero_compte_iban': 'BE4306899999950'},
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', 'Invalid IBAN')

    def test_accounting_form_with_incomplete_bank_account_for_other_format(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_autre_format', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'code_bic_swift_banque', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_unnecessary_bank_account_fields(self):
        response = self.client.post(
            self.update_url,
            data={
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertEqual(form.cleaned_data.get('numero_compte_iban'), '')
        self.assertEqual(form.cleaned_data.get('numero_compte_autre_format'), '')
        self.assertEqual(form.cleaned_data.get('code_bic_swift_banque'), '')
        self.assertEqual(form.cleaned_data.get('prenom_titulaire_compte'), '')
        self.assertEqual(form.cleaned_data.get('nom_titulaire_compte'), '')


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class GeneralAccountingViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition = MagicMock(
            uuid=str(uuid.uuid4()),
            formation=MagicMock(
                annee=2020,
                intitule='Formation',
                campus='Mons',
                sigle='TR1',
                type=TrainingType.MASTER_M1.name,
            ),
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionFormationGenerale.IN_PROGRESS.name,
            links={'update_accounting': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={},
        )

        cls.accounting = {
            'attestation_absence_dette_etablissement': ['attestation_absence_dette_etablissement.pdf'],
            'demande_allocation_d_etudes_communaute_francaise_belgique': False,
            'enfant_personnel': False,
            'attestation_enfant_personnel': ['attestation_enfant_personnel.pdf'],
            'type_situation_assimilation': TypeSituationAssimilation.AUCUNE_ASSIMILATION.name,
            'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
            'carte_resident_longue_duree': ['carte_resident_longue_duree.pdf'],
            'carte_cire_sejour_illimite_etranger': ['carte_cire_sejour_illimite_etranger.pdf'],
            'carte_sejour_membre_ue': ['carte_sejour_membre_ue.pdf'],
            'carte_sejour_permanent_membre_ue': ['carte_sejour_permanent_membre_ue.pdf'],
            'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
            'carte_a_b_refugie': ['carte_a_b_refugie.pdf'],
            'annexe_25_26_refugies_apatrides': ['annexe_25_26_refugies_apatrides.pdf'],
            'attestation_immatriculation': ['attestation_immatriculation.pdf'],
            'carte_a_b': ['carte_a_b.pdf'],
            'decision_protection_subsidiaire': ['decision_protection_subsidiaire.pdf'],
            'decision_protection_temporaire': ['decision_protection_temporaire.pdf'],
            'sous_type_situation_assimilation_3': (
                ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
            ),
            'titre_sejour_3_mois_professionel': ['titre_sejour_3_mois_professionel.pdf'],
            'fiches_remuneration': ['fiches_remuneration.pdf'],
            'titre_sejour_3_mois_remplacement': ['titre_sejour_3_mois_remplacement.pdf'],
            'preuve_allocations_chomage_pension_indemnite': ['preuve_allocations_chomage_pension_indemnite.pdf'],
            'attestation_cpas': ['attestation_cpas.pdf'],
            'relation_parente': LienParente.MERE.name,
            'sous_type_situation_assimilation_5': ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'composition_menage_acte_naissance': ['composition_menage_acte_naissance.pdf'],
            'acte_tutelle': ['acte_tutelle.pdf'],
            'composition_menage_acte_mariage': ['composition_menage_acte_mariage.pdf'],
            'attestation_cohabitation_legale': ['attestation_cohabitation_legale.pdf'],
            'carte_identite_parent': ['carte_identite_parent.pdf'],
            'titre_sejour_longue_duree_parent': ['titre_sejour_longue_duree_parent.pdf'],
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [
                'annexe_25_26_refugies_apatrides_decision_protection_parent.pdf'
            ],
            'titre_sejour_3_mois_parent': ['titre_sejour_3_mois_parent.pdf'],
            'fiches_remuneration_parent': ['fiches_remuneration_parent.pdf'],
            'attestation_cpas_parent': ['attestation_cpas_parent.pdf'],
            'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
            'decision_bourse_cfwb': ['decision_bourse_cfwb.pdf'],
            'attestation_boursier': ['attestation_boursier.pdf'],
            'titre_identite_sejour_longue_duree_ue': ['titre_identite_sejour_longue_duree_ue.pdf'],
            'titre_sejour_belgique': ['titre_sejour_belgique.pdf'],
            'affiliation_sport': ChoixAffiliationSport.MONS.name,
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            'numero_compte_iban': 'BE87001431855594',
            'iban_valide': True,
            'numero_compte_autre_format': '0123456789',
            'code_bic_swift_banque': 'GEBABEBB',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
            'derniers_etablissements_superieurs_communaute_fr_frequentes': {
                'names': ['Institut de technologie', 'Institut de pharmacologie'],
                'academic_year': 2021,
            },
            'a_nationalite_ue': False,
        }

        cls.detail_url = resolve_url('admission:general-education:accounting', pk=cls.proposition.uuid)
        cls.update_url = resolve_url('admission:general-education:update:accounting', pk=cls.proposition.uuid)

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.retrieve_general_accounting.return_value.to_dict.return_value = (
            self.accounting
        )

        self.addCleanup(propositions_api_patcher.stop)

        # Mock osis document api
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock iban validator
        iban_validator_patcher = patch("admission.contrib.forms.accounting.IBANValidatorService.validate")
        self.mock_iban_validator = iban_validator_patcher.start()
        self.mock_iban_validator.side_effect = validate_ok
        # self.mock_iban_validator.return_value.validate.return_value = True
        self.addCleanup(iban_validator_patcher.stop)

        self.client.force_login(self.person.user)

    def test_display_accounting_details(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_general_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context['admission'], self.proposition)
        self.assertEqual(response.context['accounting'], self.accounting)
        self.assertEqual(response.context['formatted_relationships'], FORMATTED_RELATIONSHIPS)
        self.assertEqual(response.context['dynamic_person_concerned_lowercase'], dynamic_person_concerned_lowercase)

    def test_display_accounting_form(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_general_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context.get('admission'), self.proposition)
        self.assertEqual(response.context.get('accounting'), self.accounting)
        self.assertEqual(response.context.get('formatted_relationships'), FORMATTED_RELATIONSHIPS)
        self.assertEqual(response.context.get('relationships'), {elt.name: elt.value for elt in LienParente})

        # Check form initialization
        form = response.context['form']
        sport_affiliation_choices = form.fields['affiliation_sport'].choices
        self.assertEqual(sport_affiliation_choices[0][0], ChoixAffiliationSport.MONS_UCL.name)
        self.assertEqual(sport_affiliation_choices[1][0], ChoixAffiliationSport.MONS.name)
        self.assertEqual(sport_affiliation_choices[2][0], ChoixAffiliationSport.NON.name)
        self.assertEqual(
            form.fields['attestation_absence_dette_etablissement'].label,
            "Attestations stipulant l'absence de dettes vis-à-vis des établissements fréquentés durant l'année "
            "académique 2021-2022 : Institut de technologie, Institut de pharmacologie.",
        )
        self.assertTrue(form.fields['attestation_absence_dette_etablissement'].required)
        self.assertTrue(form.fields['type_situation_assimilation'].required)

    def test_post_accounting_form_with_valid_data(self):
        data = {
            'attestation_absence_dette_etablissement_0': ['file.pdf'],
            'demande_allocation_d_etudes_communaute_francaise_belgique': False,
            'enfant_personnel': True,
            'attestation_enfant_personnel_0': ['file.pdf'],
            'type_situation_assimilation': TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'attestation_cpas_0': ['file.pdf'],
            'affiliation_sport': ChoixAffiliationSport.NON.name,
            'etudiant_solidaire': False,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_autre_format': '123456',
            'code_bic_swift_banque': 'GKCCBEBB',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
        }

        response = self.client.post(self.update_url, data=data)

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        command_params = {
            'uuid_proposition': self.proposition.uuid,
            'attestation_absence_dette_etablissement': ['file.pdf'],
            'demande_allocation_d_etudes_communaute_francaise_belgique': False,
            'enfant_personnel': True,
            'attestation_enfant_personnel': ['file.pdf'],
            'type_situation_assimilation': TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            'sous_type_situation_assimilation_1': '',
            'carte_resident_longue_duree': [],
            'carte_cire_sejour_illimite_etranger': [],
            'carte_sejour_membre_ue': [],
            'carte_sejour_permanent_membre_ue': [],
            'sous_type_situation_assimilation_2': '',
            'carte_a_b_refugie': [],
            'annexe_25_26_refugies_apatrides': [],
            'attestation_immatriculation': [],
            'carte_a_b': [],
            'decision_protection_subsidiaire': [],
            'decision_protection_temporaire': [],
            'sous_type_situation_assimilation_3': '',
            'titre_sejour_3_mois_professionel': [],
            'fiches_remuneration': [],
            'titre_sejour_3_mois_remplacement': [],
            'preuve_allocations_chomage_pension_indemnite': [],
            'attestation_cpas': ['file.pdf'],
            'relation_parente': '',
            'sous_type_situation_assimilation_5': '',
            'composition_menage_acte_naissance': [],
            'acte_tutelle': [],
            'composition_menage_acte_mariage': [],
            'attestation_cohabitation_legale': [],
            'carte_identite_parent': [],
            'titre_sejour_longue_duree_parent': [],
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [],
            'titre_sejour_3_mois_parent': [],
            'fiches_remuneration_parent': [],
            'attestation_cpas_parent': [],
            'sous_type_situation_assimilation_6': '',
            'decision_bourse_cfwb': [],
            'attestation_boursier': [],
            'titre_identite_sejour_longue_duree_ue': [],
            'titre_sejour_belgique': [],
            'affiliation_sport': ChoixAffiliationSport.NON.name,
            'etudiant_solidaire': False,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_iban': '',
            'iban_valide': None,
            'numero_compte_autre_format': '123456',
            'code_bic_swift_banque': 'GKCCBEBB',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
        }

        self.mock_proposition_api.return_value.update_general_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_generale_command=command_params,
            **self.default_kwargs,
        )

        # Valid IBAN
        self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        command_params['type_numero_compte'] = ChoixTypeCompteBancaire.IBAN.name
        command_params['numero_compte_iban'] = 'BE43068999999501'
        command_params['code_bic_swift_banque'] = ''
        command_params['numero_compte_autre_format'] = ''
        command_params['iban_valide'] = True

        self.mock_proposition_api.return_value.update_general_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_generale_command=command_params,
            **self.default_kwargs,
        )

        # The IBAN validator doesn't work
        self.mock_iban_validator.side_effect = validate_with_no_service_exception

        self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        command_params['type_numero_compte'] = ChoixTypeCompteBancaire.IBAN.name
        command_params['numero_compte_iban'] = 'BE43068999999501'
        command_params['code_bic_swift_banque'] = ''
        command_params['numero_compte_autre_format'] = ''
        command_params['iban_valide'] = None

        self.mock_proposition_api.return_value.update_general_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_generale_command=command_params,
            **self.default_kwargs,
        )

    def test_accounting_form_with_no_data(self):
        response = self.client.post(self.update_url, data={})

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        for field in [
            'attestation_absence_dette_etablissement',
            'demande_allocation_d_etudes_communaute_francaise_belgique',
            'enfant_personnel',
            'type_situation_assimilation',
            'affiliation_sport',
            'etudiant_solidaire',
            'type_numero_compte',
        ]:
            self.assertFormError(response, 'form', field, FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_no_data_ue_country_and_no_previous_highschool(self):
        mock_accounting = (
            self.mock_proposition_api.return_value.retrieve_general_accounting.return_value.to_dict.return_value
        )
        mock_accounting['derniers_etablissements_superieurs_communaute_fr_frequentes'] = None
        mock_accounting['a_nationalite_ue'] = True

        response = self.client.post(self.update_url, data={})

        # Check the form
        form = response.context.get('form')
        self.assertFalse(form.fields['attestation_absence_dette_etablissement'].required)
        self.assertFalse(form.fields['type_situation_assimilation'].required)
        self.assertIsNone(form.errors.get('attestation_absence_dette_etablissement'))
        self.assertIsNone(form.errors.get('type_situation_assimilation'))

    def test_accounting_form_with_incomplete_registration_fees_fields(self):
        response = self.client.post(
            self.update_url,
            data={
                'enfant_personnel': True,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'attestation_enfant_personnel', FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_unecessary_registration_fees_fields(self):
        response = self.client.post(
            self.update_url,
            data={
                'enfant_personnel': False,
                'attestation_enfant_personnel': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertEqual(form.cleaned_data.get('attestation_enfant_personnel'), [])

    def test_accounting_form_with_incomplete_bank_account_for_iban(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_with_invalid_iban(self):
        # The IBAN is not valid
        self.mock_iban_validator.side_effect = validate_with_invalid_iban_exception

        response = self.client.post(
            self.update_url,
            data={'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name, 'numero_compte_iban': 'BE4306899999950'},
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', 'Invalid IBAN')

    def test_accounting_form_with_incomplete_bank_account_for_other_format(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_autre_format', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'code_bic_swift_banque', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_unnecessary_bank_account_fields(self):
        response = self.client.post(
            self.update_url,
            data={
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertEqual(form.cleaned_data.get('numero_compte_iban'), '')
        self.assertEqual(form.cleaned_data.get('numero_compte_autre_format'), '')
        self.assertEqual(form.cleaned_data.get('code_bic_swift_banque'), '')
        self.assertEqual(form.cleaned_data.get('prenom_titulaire_compte'), '')
        self.assertEqual(form.cleaned_data.get('nom_titulaire_compte'), '')

    def test_accounting_form_with_incomplete_assimilation_1(self):
        default_data = {
            'type_situation_assimilation': (
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name
            ),
            'carte_resident_longue_duree': ['carte_resident_longue_duree.pdf'],
            'carte_cire_sejour_illimite_etranger': ['carte_cire_sejour_illimite_etranger.pdf'],
            'carte_sejour_membre_ue': ['carte_sejour_membre_ue.pdf'],
            'carte_sejour_permanent_membre_ue': ['carte_sejour_permanent_membre_ue.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE.name,
                'carte_resident_longue_duree': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_resident_longue_duree', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_cire_sejour_illimite_etranger'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_membre_ue'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_permanent_membre_ue'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_ETRANGER.name,
                'carte_cire_sejour_illimite_etranger': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_cire_sejour_illimite_etranger', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_resident_longue_duree'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_membre_ue'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_permanent_membre_ue'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_1': ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_MEMBRE_UE.name,
                'carte_sejour_membre_ue': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_sejour_membre_ue', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_resident_longue_duree'), [])
        self.assertEqual(form.cleaned_data.get('carte_cire_sejour_illimite_etranger'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_permanent_membre_ue'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_1': (
                    ChoixAssimilation1.TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE.name
                ),
                'carte_sejour_permanent_membre_ue': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_sejour_permanent_membre_ue', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_resident_longue_duree'), [])
        self.assertEqual(form.cleaned_data.get('carte_cire_sejour_illimite_etranger'), [])
        self.assertEqual(form.cleaned_data.get('carte_sejour_membre_ue'), [])

    def test_accounting_form_with_incomplete_assimilation_2(self):
        default_data = {
            'type_situation_assimilation': (
                TypeSituationAssimilation.REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
            ),
            'carte_a_b_refugie': ['carte_a_b_refugie.pdf'],
            'annexe_25_26_refugies_apatrides': ['annexe_25_26_refugies_apatrides.pdf'],
            'attestation_immatriculation': ['attestation_immatriculation.pdf'],
            'carte_a_b': ['carte_a_b.pdf'],
            'decision_protection_subsidiaire': ['decision_protection_subsidiaire.pdf'],
            'decision_protection_temporaire': ['decision_protection_temporaire.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.REFUGIE.name,
                'carte_a_b_refugie': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_a_b_refugie', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides'), [])
        self.assertEqual(form.cleaned_data.get('attestation_immatriculation'), [])
        self.assertEqual(form.cleaned_data.get('carte_a_b'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_subsidiaire'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_temporaire'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.DEMANDEUR_ASILE.name,
                'annexe_25_26_refugies_apatrides': [],
                'attestation_immatriculation': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'annexe_25_26_refugies_apatrides', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'attestation_immatriculation', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_a_b_refugie'), [])
        self.assertEqual(form.cleaned_data.get('carte_a_b'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_subsidiaire'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_temporaire'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name,
                'carte_a_b': [],
                'decision_protection_subsidiaire': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_a_b', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'decision_protection_subsidiaire', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_a_b_refugie'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides'), [])
        self.assertEqual(form.cleaned_data.get('attestation_immatriculation'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_temporaire'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_2': ChoixAssimilation2.PROTECTION_TEMPORAIRE.name,
                'decision_protection_temporaire': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'decision_protection_temporaire', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_a_b_refugie'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides'), [])
        self.assertEqual(form.cleaned_data.get('attestation_immatriculation'), [])
        self.assertEqual(form.cleaned_data.get('carte_a_b'), [])
        self.assertEqual(form.cleaned_data.get('decision_protection_subsidiaire'), [])

    def test_accounting_form_with_incomplete_assimilation_3(self):
        default_data = {
            'type_situation_assimilation': (
                TypeSituationAssimilation.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
            ),
            'titre_sejour_3_mois_professionel': ['titre_sejour_3_mois_professionel.pdf'],
            'fiches_remuneration': ['fiches_remuneration.pdf'],
            'titre_sejour_3_mois_remplacement': ['titre_sejour_3_mois_remplacement.pdf'],
            'preuve_allocations_chomage_pension_indemnite': ['preuve_allocations_chomage_pension_indemnite.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS.name
                ),
                'titre_sejour_3_mois_professionel': [],
                'fiches_remuneration': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'titre_sejour_3_mois_professionel', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'fiches_remuneration', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_remplacement'), [])
        self.assertEqual(form.cleaned_data.get('preuve_allocations_chomage_pension_indemnite'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_3': (
                    ChoixAssimilation3.AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT.name
                ),
                'titre_sejour_3_mois_remplacement': [],
                'preuve_allocations_chomage_pension_indemnite': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'titre_sejour_3_mois_remplacement', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'preuve_allocations_chomage_pension_indemnite', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_professionel'), [])
        self.assertEqual(form.cleaned_data.get('fiches_remuneration'), [])

    def test_accounting_form_with_incomplete_assimilation_4(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_situation_assimilation': TypeSituationAssimilation.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'attestation_cpas', FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_incomplete_assimilation_5_relation_parente(self):
        default_data = {
            'type_situation_assimilation': (
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
            ),
            'composition_menage_acte_naissance': ['composition_menage_acte_naissance.pdf'],
            'acte_tutelle': ['acte_tutelle.pdf'],
            'composition_menage_acte_mariage': ['composition_menage_acte_mariage.pdf'],
            'attestation_cohabitation_legale': ['attestation_cohabitation_legale.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'relation_parente': LienParente.PERE.name,
                'composition_menage_acte_naissance': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'composition_menage_acte_naissance', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('acte_tutelle'), [])
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_mariage'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cohabitation_legale'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'relation_parente': LienParente.MERE.name,
                'composition_menage_acte_naissance': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'composition_menage_acte_naissance', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('acte_tutelle'), [])
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_mariage'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cohabitation_legale'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'relation_parente': LienParente.TUTEUR_LEGAL.name,
                'acte_tutelle': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'acte_tutelle', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_naissance'), [])
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_mariage'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cohabitation_legale'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'relation_parente': LienParente.COHABITANT_LEGAL.name,
                'attestation_cohabitation_legale': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'attestation_cohabitation_legale', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_naissance'), [])
        self.assertEqual(form.cleaned_data.get('acte_tutelle'), [])
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_mariage'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'relation_parente': LienParente.CONJOINT.name,
                'composition_menage_acte_mariage': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'composition_menage_acte_mariage', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('composition_menage_acte_naissance'), [])
        self.assertEqual(form.cleaned_data.get('acte_tutelle'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cohabitation_legale'), [])

    def test_accounting_form_with_incomplete_assimilation_5(self):
        default_data = {
            'type_situation_assimilation': (
                TypeSituationAssimilation.PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4.name
            ),
            'carte_identite_parent': ['carte_identite_parent.pdf'],
            'titre_sejour_longue_duree_parent': ['titre_sejour_longue_duree_parent.pdf'],
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [
                'annexe_25_26_refugies_apatrides_decision_protection_parent.pdf'
            ],
            'titre_sejour_3_mois_parent': ['titre_sejour_3_mois_parent.pdf'],
            'fiches_remuneration_parent': ['fiches_remuneration_parent.pdf'],
            'attestation_cpas_parent': ['attestation_cpas_parent.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.A_NATIONALITE_UE.name,
                'carte_identite_parent': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'carte_identite_parent', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('titre_sejour_longue_duree_parent'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides_decision_protection_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_parent'), [])
        self.assertEqual(form.cleaned_data.get('fiches_remuneration_parent'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cpas_parent'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE.name,
                'titre_sejour_longue_duree_parent': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'titre_sejour_longue_duree_parent', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_identite_parent'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides_decision_protection_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_parent'), [])
        self.assertEqual(form.cleaned_data.get('fiches_remuneration_parent'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cpas_parent'), [])

        data = {
            **default_data,
            'sous_type_situation_assimilation_5': (
                ChoixAssimilation5.CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE.name
            ),
            'annexe_25_26_refugies_apatrides_decision_protection_parent': [],
        }

        response = self.client.post(
            self.update_url,
            data=data,
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(
            response, 'form', 'annexe_25_26_refugies_apatrides_decision_protection_parent', FIELD_REQUIRED_MESSAGE
        )

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_identite_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_longue_duree_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_parent'), [])
        self.assertEqual(form.cleaned_data.get('fiches_remuneration_parent'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cpas_parent'), [])

        data = {
            **default_data,
            'sous_type_situation_assimilation_5': (
                ChoixAssimilation5.AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT.name
            ),
            'titre_sejour_3_mois_parent': [],
            'fiches_remuneration_parent': [],
        }

        response = self.client.post(
            self.update_url,
            data=data,
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'titre_sejour_3_mois_parent', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'fiches_remuneration_parent', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_identite_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_longue_duree_parent'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides_decision_protection_parent'), [])
        self.assertEqual(form.cleaned_data.get('attestation_cpas_parent'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_5': ChoixAssimilation5.PRIS_EN_CHARGE_OU_DESIGNE_CPAS.name,
                'attestation_cpas_parent': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'attestation_cpas_parent', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('carte_identite_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_longue_duree_parent'), [])
        self.assertEqual(form.cleaned_data.get('annexe_25_26_refugies_apatrides_decision_protection_parent'), [])
        self.assertEqual(form.cleaned_data.get('titre_sejour_3_mois_parent'), [])
        self.assertEqual(form.cleaned_data.get('fiches_remuneration_parent'), [])

    def test_accounting_form_with_incomplete_assimilation_6(self):
        default_data = {
            'type_situation_assimilation': TypeSituationAssimilation.A_BOURSE_ARTICLE_105_PARAGRAPH_2.name,
            'decision_bourse_cfwb': ['decision_bourse_cfwb.pdf'],
            'attestation_boursier': ['attestation_boursier.pdf'],
        }

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE.name,
                'decision_bourse_cfwb': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'decision_bourse_cfwb', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('attestation_boursier'), [])

        response = self.client.post(
            self.update_url,
            data={
                **default_data,
                'sous_type_situation_assimilation_6': ChoixAssimilation6.A_BOURSE_COOPERATION_DEVELOPPEMENT.name,
                'attestation_boursier': [],
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'attestation_boursier', FIELD_REQUIRED_MESSAGE)

        # Check that the unnecessary fields are clean
        form = response.context.get('form')
        self.assertEqual(form.cleaned_data.get('decision_bourse_cfwb'), [])

    def test_accounting_form_with_incomplete_assimilation_7(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_situation_assimilation': TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check that the form has the specific error
        self.assertFormError(response, 'form', 'titre_identite_sejour_longue_duree_ue', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'titre_sejour_belgique', FIELD_REQUIRED_MESSAGE)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ContinuingAccountingViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition = MagicMock(
            uuid=str(uuid.uuid4()),
            formation=MagicMock(
                annee=2020,
                intitule='Formation',
                campus='Mons',
                sigle='TR1',
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            ),
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionFormationContinue.IN_PROGRESS.name,
            links={'update_accounting': {'url': 'ok'}},
            erreurs={},
            reponses_questions_specifiques={},
        )

        cls.accounting = {
            'etudiant_solidaire': True,
            'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            'numero_compte_iban': 'BE87001431855594',
            'iban_valide': True,
            'numero_compte_autre_format': '0123456789',
            'code_bic_swift_banque': 'GEBABEBB',
            'prenom_titulaire_compte': 'John',
            'nom_titulaire_compte': 'Doe',
        }

        cls.detail_url = resolve_url('admission:continuing-education:accounting', pk=cls.proposition.uuid)
        cls.update_url = resolve_url('admission:continuing-education:update:accounting', pk=cls.proposition.uuid)

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        api_ret = self.mock_proposition_api.return_value
        api_ret.retrieve_continuing_education_proposition.return_value = self.proposition
        api_ret.retrieve_continuing_accounting.return_value.to_dict.return_value = self.accounting

        self.addCleanup(propositions_api_patcher.stop)

        # Mock osis document api
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock iban validator
        iban_validator_patcher = patch("admission.contrib.forms.accounting.IBANValidatorService.validate")
        self.mock_iban_validator = iban_validator_patcher.start()
        self.mock_iban_validator.side_effect = validate_ok
        self.addCleanup(iban_validator_patcher.stop)

        self.client.force_login(self.person.user)

    def test_display_accounting_details(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_continuing_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context['admission'], self.proposition)
        self.assertEqual(response.context['accounting'], self.accounting)
        self.assertEqual(response.context['formatted_relationships'], FORMATTED_RELATIONSHIPS)
        self.assertEqual(response.context['dynamic_person_concerned_lowercase'], dynamic_person_concerned_lowercase)

    def test_display_accounting_form(self):
        response = self.client.get(self.update_url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.retrieve_continuing_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        # Check context data
        self.assertEqual(response.context.get('admission'), self.proposition)
        self.assertEqual(response.context.get('accounting'), self.accounting)
        self.assertEqual(response.context.get('relationships'), {elt.name: elt.value for elt in LienParente})
        self.assertEqual(response.context.get('formatted_relationships'), FORMATTED_RELATIONSHIPS)

    def test_post_accounting_form_with_valid_data(self):
        data = {
            'etudiant_solidaire': False,
            'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            'numero_compte_autre_format': '123456',
            'numero_compte_iban': 'BE87001431855590',
            'code_bic_swift_banque': 'GKCCBEBA',
            'prenom_titulaire_compte': 'Jim',
            'nom_titulaire_compte': 'Foe',
        }

        response = self.client.post(self.update_url, data=data)

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        self.mock_proposition_api.return_value.update_continuing_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_continue_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_continuing_accounting.call_args[1][
            'completer_comptabilite_proposition_continue_command'
        ]

        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.AUTRE_FORMAT.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '123456')
        self.assertEqual(command_args['numero_compte_iban'], '')
        self.assertEqual(command_args['code_bic_swift_banque'], 'GKCCBEBA')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], True)

        # Valid IBAN
        response = self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        self.mock_proposition_api.return_value.update_continuing_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_continue_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_continuing_accounting.call_args[1][
            'completer_comptabilite_proposition_continue_command'
        ]

        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.IBAN.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '')
        self.assertEqual(command_args['numero_compte_iban'], 'BE43068999999501')
        self.assertEqual(command_args['code_bic_swift_banque'], '')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], True)

        # The IBAN validator doesn't work
        self.mock_iban_validator.side_effect = validate_with_no_service_exception

        response = self.client.post(
            self.update_url,
            data={
                **data,
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
                'numero_compte_iban': 'BE43068999999501',
            },
        )

        # Check status and redirection
        self.assertRedirects(response, self.update_url)

        # Check API calls
        self.mock_proposition_api.return_value.update_continuing_accounting.assert_called_with(
            uuid=self.proposition.uuid,
            completer_comptabilite_proposition_continue_command=ANY,
            **self.default_kwargs,
        )

        command_args = self.mock_proposition_api.return_value.update_continuing_accounting.call_args[1][
            'completer_comptabilite_proposition_continue_command'
        ]

        self.assertEqual(command_args['etudiant_solidaire'], False)
        self.assertEqual(command_args['type_numero_compte'], ChoixTypeCompteBancaire.IBAN.name)
        self.assertEqual(command_args['numero_compte_autre_format'], '')
        self.assertEqual(command_args['numero_compte_iban'], 'BE43068999999501')
        self.assertEqual(command_args['code_bic_swift_banque'], '')
        self.assertEqual(command_args['prenom_titulaire_compte'], 'Jim')
        self.assertEqual(command_args['nom_titulaire_compte'], 'Foe')
        self.assertEqual(command_args['iban_valide'], None)

    def test_accounting_form_with_no_data(self):
        response = self.client.post(self.update_url, data={})

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())

        missing_fields = [
            'etudiant_solidaire',
            'type_numero_compte',
        ]
        self.assertCountEqual(missing_fields, form.errors.keys())
        for field in missing_fields:
            self.assertFormError(response, 'form', field, FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_incomplete_bank_account_for_iban(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_with_invalid_iban(self):
        # The IBAN is not valid
        self.mock_iban_validator.side_effect = validate_with_invalid_iban_exception

        response = self.client.post(
            self.update_url,
            data={'type_numero_compte': ChoixTypeCompteBancaire.IBAN.name, 'numero_compte_iban': 'BE4306899999950'},
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_iban', 'Invalid IBAN')

    def test_accounting_form_with_incomplete_bank_account_for_other_format(self):
        response = self.client.post(
            self.update_url,
            data={
                'type_numero_compte': ChoixTypeCompteBancaire.AUTRE_FORMAT.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertFalse(form.is_valid())
        self.assertFormError(response, 'form', 'numero_compte_autre_format', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'code_bic_swift_banque', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'form', 'nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)

    def test_accounting_form_with_unnecessary_bank_account_fields(self):
        response = self.client.post(
            self.update_url,
            data={
                'numero_compte_iban': 'BE43068999999501',
                'numero_compte_autre_format': '123456',
                'code_bic_swift_banque': 'GKCCBEBB',
                'prenom_titulaire_compte': 'John',
                'nom_titulaire_compte': 'Doe',
            },
        )

        self.assertEqual(response.status_code, 200)

        # Check the form
        form = response.context.get('form')

        self.assertEqual(form.cleaned_data.get('numero_compte_iban'), '')
        self.assertEqual(form.cleaned_data.get('numero_compte_autre_format'), '')
        self.assertEqual(form.cleaned_data.get('code_bic_swift_banque'), '')
        self.assertEqual(form.cleaned_data.get('prenom_titulaire_compte'), '')
        self.assertEqual(form.cleaned_data.get('nom_titulaire_compte'), '')
