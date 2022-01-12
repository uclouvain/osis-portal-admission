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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites
from rest_framework import status

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.financement import BourseRecherche, ChoixTypeContratTravail, ChoixTypeFinancement
from admission.contrib.enums.projet import ChoixStatusProposition
from admission.contrib.enums.proximity_commission import ChoixProximityCommissionCDE, ChoixProximityCommissionCDSS
from admission.services.proposition import PropositionBusinessException
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import ApiBusinessException, MultipleApiBusinessException


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ProjectViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.mock_entities = [
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

    def setUp(self):
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
            links={},
        )
        self.addCleanup(propositions_api_patcher.stop)

        # Mock admission sdk api
        autocomplete_api_patcher = patch("osis_admission_sdk.api.autocomplete_api.AutocompleteApi")
        self.mock_autocomplete_api = autocomplete_api_patcher.start()
        self.mock_autocomplete_api.return_value.list_sector_dtos.return_value = [
            Mock(sigle='SSH', intitule_fr='Foobar', intitule_en='Foobar'),
            Mock(sigle='SST', intitule_fr='Barbaz', intitule_en='Barbaz'),
            Mock(sigle='SSS', intitule_fr='Foobarbaz', intitule_en='Foobarbaz'),
        ]
        self.mock_autocomplete_api.return_value.list_doctorat_dtos.return_value = [
            Mock(
                sigle='FOOBAR',
                intitule_fr='Foobar',
                intitule_en='Foobar',
                annee=2021,
                sigle_entite_gestion="CDE",
                links=[],
            ),
            Mock(
                sigle='FOOBARBAZ',
                intitule_fr='Foobarbaz',
                intitule_en='Foobarbaz',
                annee=2021,
                sigle_entite_gestion="CDSS",
                links=[],
            ),
            Mock(
                sigle='BARBAZ',
                intitule_fr='Barbaz',
                intitule_en='Barbaz',
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

        self.client.force_login(self.person.user)

    def test_create(self):
        url = resolve_url('admission:doctorate-create:project')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'SSH')

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'FOOBAR-2021',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'commission_proximite_cde', _("This field is required."))
        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'FOOBARBAZ-2021',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'commission_proximite_cdss', _("This field is required."))

        self.mock_proposition_api.return_value.create_proposition.return_value = {
            'uuid': "3c5cdc60-2537-4a12-a396-64d2e9e34876",
        }
        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        expected_url = resolve_url('admission:doctorate-update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        self.mock_proposition_api.return_value.create_proposition.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(
                    status_code=PropositionBusinessException.JustificationRequiseException.value,
                    detail="Something wrong on a field"
                ),
                ApiBusinessException(
                    status_code=42,
                    detail="Something went wrong globally"
                ),
            }
        )
        response = self.client.post(url, {
            'type_admission': AdmissionType.PRE_ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Something wrong on a field")
        self.assertContains(response, "Something went wrong globally")

    def test_update(self):
        url = resolve_url('admission:doctorate-update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        self.mock_proposition_api.return_value.retrieve_proposition.return_value.sigle_doctorat = 'FOOBAR'
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.annee_doctorat = '2021'
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.code_secteur_formation = 'SSH'
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'code_secteur_formation': "SSH",
            'type_contrat_travail': "Something",
            "commission_proximite": ChoixProximityCommissionCDE.ECONOMY.name,
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mock_proposition_api.return_value.retrieve_proposition.return_value.sigle_doctorat = 'FOOBARBAZ'
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'code_secteur_formation': "SSH",
            'sigle_doctorat': 'FOOBARBAZ',
            'annee_doctorat': '2021',
            'bourse_recherche': "Something other",
            "commission_proximite": ChoixProximityCommissionCDSS.ECLI.name,
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the thesis institute field is well initialized with existing value
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'code_secteur_formation': "SST",
            'type_contrat_travail': "Something",
            'institut_these': self.mock_entities[0].uuid,
            'lieu_these': 'A random postal address',
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "{title} ({acronym})".format_map(self.mock_entities[0]))
        self.assertContains(response, "A random postal address")

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_update_consistency_errors(self):
        url = resolve_url('admission:doctorate-update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'code_secteur_formation': "SST",
        }

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
        })
        self.assertFormError(response, 'form', 'type_contrat_travail', _("This field is required."))
        self.assertFormError(response, 'form', 'eft', _("This field is required."))

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
        })
        self.assertFormError(response, 'form', 'eft', _("This field is required."))

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.OTHER.name,
        })
        self.assertFormError(response, 'form', 'type_contrat_travail_other', _("This field is required."))

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_ASSISTANT.name,
            'eft': 80,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
        })
        self.assertFormError(response, 'form', 'bourse_recherche', _("This field is required."))

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'bourse_recherche': BourseRecherche.OTHER.name,
        })
        self.assertFormError(response, 'form', 'bourse_recherche_other', _("This field is required."))

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.SEARCH_SCHOLARSHIP.name,
            'bourse_recherche': BourseRecherche.ARES.name,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_detail(self):
        url = resolve_url('admission:doctorate-detail:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
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
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Proximity commission for experimental and clinical research (ECLI)"))

    def test_cancel(self):
        url = resolve_url('admission:doctorate-cancel', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            statut=ChoixStatusProposition.IN_PROGRESS.name,
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, ChoixStatusProposition.IN_PROGRESS.value)
        self.mock_proposition_api.return_value.destroy_proposition.assert_not_called()
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_proposition_api.return_value.destroy_proposition.assert_called()
