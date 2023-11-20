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
from unittest.mock import MagicMock, Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites
from rest_framework import status

from admission.contrib.enums.admission_type import AdmissionType
from admission.contrib.enums.financement import ChoixTypeContratTravail, ChoixTypeFinancement
from admission.contrib.enums.projet import (
    ChoixStatutPropositionDoctorale,
    ChoixStatutPropositionContinue,
    ChoixStatutPropositionGenerale,
)
from admission.contrib.enums.proximity_commission import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixSousDomaineSciences,
)
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.training_choice import TrainingType
from admission.contrib.forms import PDF_MIME_TYPE
from admission.contrib.forms.project import COMMISSION_CDSS, SCIENCE_DOCTORATE
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ProjectViewTestCase(TestCase):
    @classmethod
    def get_scholarship(cls, uuid, **kwargs):
        return next((scholarship for scholarship in cls.mock_scholarships if scholarship.uuid == uuid), None)

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        cls.doctorate_international_scholarship = MagicMock(
            uuid=str(uuid.uuid4()),
            short_name="ARC",
            long_name="ARC",
            type=TypeBourse.BOURSE_INTERNATIONALE_DOCTORAT.name,
        )

        cls.mock_scholarships = [
            cls.doctorate_international_scholarship,
        ]

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
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            code_secteur_formation="SSH",
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            links={'update_proposition': {'url': 'ok'}},
            bourse_recherche=Mock(uuid=self.doctorate_international_scholarship.uuid),
            erreurs=[],
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
                type=TrainingType.PHD.name,
            ),
            Mock(
                sigle='FOOBARBAZ',
                intitule='Foobarbaz',
                annee=2021,
                sigle_entite_gestion=COMMISSION_CDSS,
                links=[],
                type=TrainingType.PHD.name,
            ),
            Mock(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
                type=TrainingType.PHD.name,
            ),
            Mock(
                sigle=SCIENCE_DOCTORATE,
                intitule='FooBarbaz',
                annee=2021,
                sigle_entite_gestion="AZERT",
                links=[],
                type=TrainingType.PHD.name,
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
        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Mock scholarship sdk api
        scholarships_api_patcher = patch("osis_admission_sdk.api.scholarship_api.ScholarshipApi")
        self.mock_scholarship_api = scholarships_api_patcher.start()
        self.mock_scholarship_api.return_value.retrieve_scholarship.side_effect = self.get_scholarship
        self.addCleanup(scholarships_api_patcher.stop)

        self.client.force_login(self.person.user)

    def test_update(self):
        url = resolve_url('admission:doctorate:update:project', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        proposition = self.mock_proposition_api.return_value.retrieve_proposition.return_value
        proposition.doctorat.sigle = 'FOOBAR'
        proposition.doctorat.annee = '2021'
        proposition.code_secteur_formation = 'SSH'
        proposition.to_dict.return_value = {
            'code_secteur_formation': "SSH",
            'type_contrat_travail': "Something",
            "commission_proximite": ChoixCommissionProximiteCDEouCLSM.ECONOMY.name,
            "raison_non_soutenue": "A very good reason",
            'bourse_recherche': str(self.doctorate_international_scholarship.uuid),
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')

        proposition.doctorat.sigle = 'FOOBARBAZ'
        proposition.to_dict.return_value = {
            "doctorat": {
                'sigle': 'FOOBARBAZ',
                'annee': '2021',
                'code_secteur_formation': "SSH",
                'type': TrainingType.PHD.name,
            },
            'bourse_recherche': str(self.doctorate_international_scholarship.uuid),
            "commission_proximite": ChoixCommissionProximiteCDSS.ECLI.name,
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, "dependsOn.min.js", count=1)

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
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
        }
        response = self.client.post(url, data)
        self.assertFormError(response, 'form', 'eft', _("This field is required."))

        data = {
            'type_admission': AdmissionType.ADMISSION.name,
            'type_financement': ChoixTypeFinancement.WORK_CONTRACT.name,
            'type_contrat_travail': ChoixTypeContratTravail.UCLOUVAIN_SCIENTIFIC_STAFF.name,
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
            'bourse_recherche': str(self.doctorate_international_scholarship.uuid),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

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
            nom_institut_these=self.mock_entities[0].title,
            sigle_institut_these=self.mock_entities[0].acronym,
            links={},
            erreurs=[],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, "Something")
        self.assertContains(response, "{title} ({acronym})".format_map(self.mock_entities[0]))
        self.assertContains(response, _("ECONOMY"))

        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            langue_redaction_these="",
            code_secteur_formation="SSS",
            commission_proximite="ECLI",
            institut_these="",
            links={},
            erreurs=[],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Proximity commission for experimental and clinical research (ECLI)"))

    def test_cancel(self):
        url = resolve_url('admission:doctorate:cancel', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            links={},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, ChoixStatutPropositionDoctorale.EN_BROUILLON.value)
        self.mock_proposition_api.return_value.destroy_proposition.assert_not_called()
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_proposition_api.return_value.destroy_proposition.assert_called()

    def test_cancel_general_education_proposition(self):
        url = resolve_url('admission:general-education:cancel', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = Mock(
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links={'destroy_proposition': {'url': 'ok'}},
        )
        response = self.client.get(url)
        self.mock_proposition_api.return_value.destroy_general_education_proposition.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, ChoixStatutPropositionGenerale.EN_BROUILLON.value)
        response = self.client.post(url, {})
        self.assertRedirects(response, expected_url=resolve_url('admission:list'))
        self.mock_proposition_api.return_value.destroy_general_education_proposition.assert_called()

    def test_cancel_continuing_education_proposition(self):
        url = resolve_url('admission:continuing-education:cancel', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value = Mock(
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            links={'destroy_proposition': {'url': 'ok'}},
        )
        response = self.client.get(url)
        self.mock_proposition_api.return_value.destroy_continuing_education_proposition.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, ChoixStatutPropositionContinue.EN_BROUILLON.value)
        response = self.client.post(url, {})
        self.assertRedirects(response, expected_url=resolve_url('admission:list'))
        self.mock_proposition_api.return_value.destroy_continuing_education_proposition.assert_called()
