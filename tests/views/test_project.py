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
import datetime
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites
from rest_framework import status

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.experience_precedente import ChoixDoctoratDejaRealise
from admission.contrib.enums.financement import BourseRecherche, ChoixTypeContratTravail, ChoixTypeFinancement
from admission.contrib.enums.projet import ChoixStatutProposition, ChoixLangueRedactionThese
from admission.contrib.enums.proximity_commission import (
    ChoixProximityCommissionCDE,
    ChoixProximityCommissionCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.forms.project import COMMISSION_CDSS, SCIENCE_DOCTORATE
from admission.services.proposition import PropositionBusinessException
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import ApiBusinessException, MultipleApiBusinessException


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ProjectViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.mock_entities = [
            Entite(
                uuid='uuid1',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of technology',
                acronym='IT',
            ),
            Entite(
                uuid='uuid2',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of foreign languages',
                acronym='IFL',
            ),
        ]
        # Mock proposition sdk api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            code_secteur_formation="SSH",
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            links={'update_proposition': {'url': 'ok'}},
        )
        self.addCleanup(propositions_api_patcher.stop)

        # Mock admission sdk api
        autocomplete_api_patcher = patch("osis_admission_sdk.api.autocomplete_api.AutocompleteApi")
        self.mock_autocomplete_api = autocomplete_api_patcher.start()
        self.mock_autocomplete_api.return_value.list_sector_dtos.return_value = [
            Mock(sigle='SSH', intitule='Foobar'),
            Mock(sigle='SST', intitule='Barbaz'),
            Mock(sigle='SSS', intitule='Foobarbaz'),
        ]
        self.mock_autocomplete_api.return_value.list_doctorat_dtos.return_value = [
            Mock(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                sigle_entite_gestion="CDE",
                links=[],
            ),
            Mock(
                sigle='FOOBARBAZ',
                intitule='Foobarbaz',
                annee=2021,
                sigle_entite_gestion=COMMISSION_CDSS,
                links=[],
            ),
            Mock(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
            ),
            Mock(
                sigle=SCIENCE_DOCTORATE,
                intitule='FooBarbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
            ),
        ]
        self.addCleanup(autocomplete_api_patcher.stop)

        # Mock organization sdk api
        organization_api_patcher = patch("osis_organisation_sdk.api.entites_api.EntitesApi")
        self.mock_organization_api = organization_api_patcher.start()
        self.mock_organization_api.return_value.get_entities.return_value = PaginatedEntites(
            results=self.mock_entities,
        )
        self.mock_organization_api.return_value.get_entity.return_value = self.mock_entities[0]
        self.addCleanup(organization_api_patcher.stop)

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()
        self.addCleanup(countries_api_patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)

        self.client.force_login(self.person.user)

    def test_create(self):
        url = resolve_url('admission:doctorate-create:project')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'SSH')

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'FOOBAR-2021',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'commission_proximite_cde', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'FOOBARBAZ-2021',
            'non_soutenue': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'commission_proximite_cdss', _("This field is required."))
        self.assertFormError(response, 'form', 'raison_non_soutenue', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'SC3DP-2021',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'sous_domaine', _("This field is required."))

        self.mock_proposition_api.return_value.create_proposition.return_value = {
            'uuid': "3c5cdc60-2537-4a12-a396-64d2e9e34876",
        }
        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'SC3DP-2021',
            'sous_domaine': ChoixSousDomaineSciences.CHEMISTRY.name,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        self.mock_proposition_api.return_value.create_proposition.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(
                    status_code=PropositionBusinessException.JustificationRequiseException.value,
                    detail="Something wrong on a field",
                ),
                ApiBusinessException(
                    status_code=42,
                    detail="Something went wrong globally",
                ),
            }
        )
        data = {
            'type_admission': AdmissionType.PRE_ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Something wrong on a field")
        self.assertContains(response, "Something went wrong globally")

    def test_sent_data_on_create(self):
        url = resolve_url('admission:doctorate-create:project')

        self.mock_proposition_api.return_value.create_proposition.return_value = {
            'uuid': "3c5cdc60-2537-4a12-a396-64d2e9e34876",
        }
        expected_url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        default_data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
            'justification': 'My justification related to the pre-admission',
            'commission_proximite_cde': ChoixProximityCommissionCDE.ECONOMY.name,
            'commission_proximite_cdss': ChoixProximityCommissionCDSS.ECLI.name,
            'sous_domaine': ChoixSousDomaineSciences.CHEMISTRY.name,
            'type_financement': ChoixTypeFinancement.SELF_FUNDING.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            'eft': 5,
            'bourse_recherche': BourseRecherche.ARC.name,
            'bourse_date_debut': '',
            'bourse_date_fin': '',
            'duree_prevue': 10,
            'temps_consacre': 20,
            'titre_projet': 'Project title',
            'lieu_these': 'Place',
            'resume_projet': 'Resume',
            'bourse_preuve_0': 'test',
            'documents_projet_0': 'test',
            'graphe_gantt_0': 'test',
            'proposition_programme_doctoral_0': 'test',
            'projet_formation_complementaire_0': 'test',
            'lettres_recommandation_0': 'test',
            'langue_redaction_these': ChoixLangueRedactionThese.ENGLISH.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.NO.name,
            'institution': 'Institution',
            'domaine_these': 'Domain',
            'non_soutenue': False,
            'date_soutenance': datetime.date(2022, 5, 1),
            'raison_non_soutenue': 'Reason',
        }

        default_kwargs = {
            'type_admission': AdmissionType.ADMISSION.name,
            'sigle_formation': 'BARBAZ',
            'annee_formation': 2021,
            'matricule_candidat': self.person.global_id,
            'justification': 'My justification related to the pre-admission',
            'commission_proximite': ChoixProximityCommissionCDE.ECONOMY.name,
            'type_financement': ChoixTypeFinancement.SELF_FUNDING.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            'eft': 5,
            'bourse_recherche': BourseRecherche.ARC.name,
            'bourse_date_debut': None,
            'bourse_date_fin': None,
            'duree_prevue': 10,
            'temps_consacre': 20,
            'titre_projet': 'Project title',
            'lieu_these': 'Place',
            'resume_projet': 'Resume',
            'bourse_preuve': ['test'],
            'documents_projet': ['test'],
            'graphe_gantt': ['test'],
            'proposition_programme_doctoral': ['test'],
            'projet_formation_complementaire': ['test'],
            'lettres_recommandation': ['test'],
            'langue_redaction_these': ChoixLangueRedactionThese.ENGLISH.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.NO.name,
            'institution': 'Institution',
            'domaine_these': 'Domain',
            'non_soutenue': False,
            'date_soutenance': datetime.date(2022, 5, 1),
            'raison_non_soutenue': 'Reason',
        }
        response = self.client.post(url, default_data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
        sent = self.mock_proposition_api.return_value.create_proposition.call_args[1]["initier_proposition_command"]
        data = {
            **default_kwargs,
            # Fields that are computed
            'commission_proximite': ChoixProximityCommissionCDE.ECONOMY.name,
            # Fields that are cleaned
            'justification': '',
            'type_contrat_travail': '',
            'eft': None,
            'bourse_recherche': '',
            'institution': '',
            'domaine_these': '',
            'non_soutenue': None,
            'date_soutenance': None,
            'raison_non_soutenue': '',
        }
        self.assertEqual(sent, data)

        data = {
            **default_data,
            'type_admission': AdmissionType.PRE_ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.YES.name,
            'non_soutenue': True,
            'commission_proximite_cde': '',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
        sent = self.mock_proposition_api.return_value.create_proposition.call_args[1]["initier_proposition_command"]
        data = {
            **default_kwargs,
            'type_admission': AdmissionType.PRE_ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.YES.name,
            'non_soutenue': True,
            # Fields that are computed
            'commission_proximite': ChoixProximityCommissionCDSS.ECLI.name,
            # Fields that are cleaned
            'bourse_recherche': '',
            'date_soutenance': None,
        }
        self.assertEqual(sent, data)

        data = {
            **default_data,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': 'Another working contract type',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
        sent = self.mock_proposition_api.return_value.create_proposition.call_args[1]["initier_proposition_command"]
        self.assertEqual(sent['type_contrat_travail'], 'Another working contract type')

        data = {
            **default_data,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.PARTIAL.name,
            'non_soutenue': False,
            'commission_proximite_cde': '',
            'commission_proximite_cdss': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
        sent = self.mock_proposition_api.return_value.create_proposition.call_args[1]["initier_proposition_command"]
        data = {
            **default_kwargs,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'doctorat_deja_realise': ChoixDoctoratDejaRealise.PARTIAL.name,
            'non_soutenue': False,
            # Fields that are computed
            'commission_proximite': ChoixSousDomaineSciences.CHEMISTRY.name,
            # Fields that are cleaned
            'justification': '',
            'type_contrat_travail': '',
            'eft': None,
            'raison_non_soutenue': '',
        }
        self.assertEqual(sent, data)

        data = {
            **default_data,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'bourse_recherche': 'Another scholarship',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)
        sent = self.mock_proposition_api.return_value.create_proposition.call_args[1]["initier_proposition_command"]
        self.assertEqual(sent['bourse_recherche'], 'Another scholarship')

    def test_update(self):
        url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        proposition = self.mock_proposition_api.return_value.retrieve_proposition.return_value
        proposition.doctorat.sigle = 'FOOBAR'
        proposition.doctorat.annee = '2021'
        proposition.code_secteur_formation = 'SSH'
        proposition.to_dict.return_value = {
            'code_secteur_formation': "SSH",
            'type_contrat_travail': "Something",
            "commission_proximite": ChoixProximityCommissionCDE.ECONOMY.name,
            "raison_non_soutenue": "A very good reason",
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposition.doctorat.sigle = 'FOOBARBAZ'
        proposition.to_dict.return_value = {
            "doctorat": {
                'sigle': 'FOOBARBAZ',
                'annee': '2021',
                'code_secteur_formation': "SSH",
            },
            'bourse_recherche': "Something other",
            "commission_proximite": ChoixProximityCommissionCDSS.ECLI.name,
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        proposition.doctorat.sigle = SCIENCE_DOCTORATE
        proposition.to_dict.return_value["commission_proximite"] = ChoixSousDomaineSciences.CHEMISTRY.name
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the thesis institute field is well initialized with existing value
        proposition.to_dict.return_value = {
            'code_secteur_formation': "SST",
            'type_contrat_travail': "Something",
            'institut_these': self.mock_entities[0].uuid,
            'lieu_these': 'A random postal address',
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "A random postal address")

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_update_no_permission(self):
        url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.links = {
            'update_proposition': {'error': 'no access'},
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_consistency_errors(self):
        url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'code_secteur_formation': "SST",
        }

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
        }
        response = self.client.post(url, data)
        self.assertFormError(response, 'form', 'type_contrat_travail', _("This field is required."))
        self.assertFormError(response, 'form', 'eft', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
        }
        response = self.client.post(url, data)
        self.assertFormError(response, 'form', 'eft', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            'eft': 80,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
        }
        response = self.client.post(url, data)
        self.assertFormError(response, 'form', 'bourse_recherche', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'bourse_recherche': BourseRecherche.ARES.name,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_project_detail_should_redirect_if_not_signing(self):
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.statut = (
            ChoixStatutProposition.IN_PROGRESS.name
        )
        url = resolve_url('admission:doctorate:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        expected_url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

    def test_detail_redirect(self):
        url = resolve_url('admission:doctorate', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        project_url = resolve_url('admission:doctorate:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, project_url)

    def test_detail(self):
        url = resolve_url('admission:doctorate:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            langue_redaction_these="",
            type_financement=ChoixTypeFinancement.WORK_CONTRACT.name,
            type_contrat_travail="Something",
            code_secteur_formation="SSH",
            commission_proximite="ECONOMY",
            institut_these=self.mock_entities[0].uuid,
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Something")
        self.assertContains(response, "{title} ({acronym})".format_map(self.mock_entities[0]))
        self.assertContains(response, _("ECONOMY"))

        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            langue_redaction_these="",
            code_secteur_formation="SSS",
            commission_proximite="ECLI",
            institut_these="",
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Proximity commission for experimental and clinical research (ECLI)"))

    def test_cancel(self):
        url = resolve_url('admission:doctorate:cancel', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            statut=ChoixStatutProposition.IN_PROGRESS.name,
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, ChoixStatutProposition.IN_PROGRESS.value)
        self.mock_proposition_api.return_value.destroy_proposition.assert_not_called()
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_proposition_api.return_value.destroy_proposition.assert_called()
