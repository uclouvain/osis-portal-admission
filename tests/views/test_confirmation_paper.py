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
from unittest.mock import Mock, patch, ANY

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings

from admission.contrib.enums.doctorat import ChoixStatutDoctorat
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ConfirmationPaperDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

        self.url = resolve_url("admission:doctorate:confirmation-paper", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'update_confirmation': {'url': 'ok'}},
            reference='21-300001',
            intitule_formation='Informatique',
            statut=ChoixStatutDoctorat.ADMITTED.name,
            sigle_formation='INFO',
            annee_formation=2022,
            matricule_doctorant='matricule_candidat_1',
            prenom_doctorant='John',
            nom_doctorantig='Doe',
            uuid='uuid1',
        )
        self.mock_api.return_value.retrieve_confirmation_papers.return_value = [
            Mock(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
            Mock(
                uuid='c2',
                date_limite='2022-05-10',
                date='2022-04-02',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
            Mock(
                uuid='c3',
                date_limite='2022-04-10',
                date='2022-04-01',
                rapport_recherche=[],
                avis_renouvellement_mandat_recherche=[],
            ),
        ]

        self.addCleanup(api_patcher.stop)

    def test_get_several_confirmation_papers(self):
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_api.return_value.retrieve_doctorate_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, 'uuid1')

        # Load the confirmation papers information
        self.mock_api.return_value.retrieve_confirmation_papers.assert_called()

        self.assertIsNotNone(response.context.get('current_confirmation_paper'))
        self.assertEqual(response.context.get('current_confirmation_paper').uuid, 'c1')

        self.assertEqual(len(response.context.get('previous_confirmation_papers')), 2)
        self.assertEqual(response.context.get('previous_confirmation_papers')[0].uuid, 'c2')
        self.assertEqual(response.context.get('previous_confirmation_papers')[1].uuid, 'c3')

    def test_get_no_confirmation_paper(self):
        self.mock_api.return_value.retrieve_confirmation_papers.return_value = []

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_api.return_value.retrieve_doctorate_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, 'uuid1')

        # Load the confirmation papers information
        self.mock_api.return_value.retrieve_confirmation_papers.assert_called()

        self.assertIsNone(response.context.get('current_confirmation_paper'))

        self.assertEqual(len(response.context.get('previous_confirmation_papers')), 0)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class ConfirmationPaperFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.api_default_params = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        self.client.force_login(self.person.user)

        self.url = resolve_url(
            "admission:doctorate:update:confirmation-paper",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
        )

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()

        self.mock_api.return_value.retrieve_doctorate_dto.return_value = Mock(
            links={'update_confirmation': {'url': 'ok'}},
            reference='21-300001',
            intitule_formation='Informatique',
            statut=ChoixStatutDoctorat.ADMITTED.name,
            sigle_formation='INFO',
            annee_formation=2022,
            matricule_doctorant='matricule_candidat_1',
            prenom_doctorant='John',
            nom_doctorantig='Doe',
            uuid='uuid1',
        )
        self.mock_api.return_value.retrieve_last_confirmation_paper.return_value = Mock(
            uuid='c1',
            date_limite='2022-06-10',
            date='2022-04-03',
            rapport_recherche=['f1'],
            avis_renouvellement_mandat_recherche=['f2'],
            proces_verbal_ca=['f3'],
            to_dict=dict(
                uuid='c1',
                date_limite='2022-06-10',
                date='2022-04-03',
                rapport_recherche=['f1'],
                avis_renouvellement_mandat_recherche=['f2'],
                proces_verbal_ca=['f3'],
            ),
        )
        self.addCleanup(api_patcher.stop)
        # Mock document api
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_several_confirmation_papers(self):
        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_api.return_value.retrieve_doctorate_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, 'uuid1')

        # Load the confirmation papers information
        self.mock_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNotNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('confirmation_paper').uuid, 'c1')

        # Initialize the form
        self.assertEqual(response.context.get('form').initial['date'], '2022-04-03')
        self.assertEqual(response.context.get('form').initial['rapport_recherche'], ['f1'])
        self.assertEqual(response.context.get('form').initial['avis_renouvellement_mandat_recherche'], ['f2'])
        self.assertEqual(response.context.get('form').initial['proces_verbal_ca'], ['f3'])

    def test_get_no_confirmation_paper(self):
        self.mock_api.return_value.retrieve_last_confirmation_paper.return_value = None

        response = self.client.get(self.url)

        # Load the doctorate information
        self.mock_api.return_value.retrieve_doctorate_dto.assert_called()
        self.assertEqual(response.context.get('doctorate').uuid, 'uuid1')

        # Load the confirmation papers information
        self.mock_api.return_value.retrieve_last_confirmation_paper.assert_called()

        self.assertIsNone(response.context.get('confirmation_paper'))
        self.assertEqual(response.context.get('form').initial, {})

    def test_post_a_confirmation_paper(self):
        self.client.post(self.url, data={
            'date': datetime.date(2022, 4, 4),
            'rapport_recherche_0': ['f11'],
            'avis_renouvellement_mandat_recherche_0': ['f22'],
            'proces_verbal_ca_0': ['f33'],
        })
        # Call the API with the right data
        self.mock_api.return_value.submit_confirmation_paper.assert_called()
        self.mock_api.return_value.submit_confirmation_paper.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            submit_confirmation_paper_command={
                'date': datetime.date(2022, 4, 4),
                'rapport_recherche': ['f11'],
                'avis_renouvellement_mandat_recherche': ['f22'],
                'proces_verbal_ca': ['f33'],

            },
            **self.api_default_params,
        )
