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
from django.test import TestCase

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.financement import ChoixTypeFinancement
from admission.services.proposition import PropositionBusinessException
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import ApiBusinessException, MultipleApiBusinessException


class ProjectViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)
        autocomplete_api_patcher = patch("osis_admission_sdk.api.autocomplete_api.AutocompleteApi")
        self.mock_autocomplete_api = autocomplete_api_patcher.start()
        self.addCleanup(autocomplete_api_patcher.stop)
        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()
        self.addCleanup(countries_api_patcher.stop)
        autocomplete_api_patcher = patch("frontoffice.settings.osis_sdk.utils.get_user_token")
        mock_user_token = autocomplete_api_patcher.start()
        mock_user_token.return_value = 'foobar'
        self.addCleanup(mock_user_token.stop)

    def test_create(self):
        url = resolve_url('admission:doctorate-create:project')
        self.client.force_login(self.person.user)
        self.mock_autocomplete_api.return_value.list_sector_dtos.return_value = [
            Mock(sigle='SSH', intitule_fr='Foobar', intitule_en='Foobar'),
            Mock(sigle='SST', intitule_fr='Barbaz', intitule_en='Barbaz'),
        ]
        self.mock_autocomplete_api.return_value.list_doctorat_dtos.return_value = [
            Mock(sigle='FOOBAR', intitule_fr='Foobar', intitule_en='Foobar', annee=2021, sigle_entite_gestion="CDE"),
            Mock(sigle='BARBAZ', intitule_fr='Barbaz', intitule_en='Barbaz', annee=2021, sigle_entite_gestion="AZERT"),
        ]
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SSH')

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
            'sector': 'SSH',
            'doctorate': 'BARBAZ-2021',
        })
        self.assertEqual(response.status_code, 302)

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
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Something wrong on a field")
        self.assertContains(response, "Something went wrong globally")

    def test_update(self):
        url = resolve_url('admission:doctorate-update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)
        self.mock_autocomplete_api.return_value.list_sector_dtos.return_value = [
            Mock(sigle='SSH', intitule_fr='Foobar', intitule_en='Foobar'),
            Mock(sigle='SST', intitule_fr='Barbaz', intitule_en='Barbaz'),
        ]
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
        )
        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'type_contrat_travail': "Something",
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.mock_proposition_api.return_value.retrieve_proposition.return_value.to_dict.return_value = {
            'bourse_recherche': "Something other"
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {
            'type_admission': AdmissionType.ADMISSION.name,
        })
        self.assertEqual(response.status_code, 302)

    def test_detail(self):
        url = resolve_url('admission:doctorate-detail:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            type_financement=ChoixTypeFinancement.WORK_CONTRACT.name,
            type_contrat_travail="Something",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Something")
