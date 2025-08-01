# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import reverse

from admission.contrib.enums import ChoixStatutPropositionDoctorale, TrainingType
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


class ListTestCase(OsisPortalTestCase):
    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_empty(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_propositions.return_value = Mock(
            doctorate_propositions=[],
            continuing_education_propositions=[],
            general_education_propositions=[],
            links={
                'create_training_choice': {'url': 'access granted'},
            },
        )
        url = reverse('admission:list')
        response = self.client.get(url)
        self.assertTrue(response.context['can_create_proposition'])
        create_url = resolve_url('admission:create')
        self.assertContains(response, create_url)

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_propositions.return_value = Mock(
            doctorate_propositions=[
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_project': {'url': 'access granted'}},
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    erreurs=[],
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                    ),
                ),
                Mock(
                    uuid='b3729603-c991-489f-8d8d-1d3a11b64dad',
                    links={},
                    erreurs=[],
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    doctorat=Mock(
                        type=TrainingType.PHD.name,
                    ),
                ),
            ],
            continuing_education_propositions=[
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    doctorat=None,
                    formation=Mock(
                        type=TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
                    ),
                ),
            ],
            general_education_propositions=[
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                    statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
                    formation=Mock(
                        type=TrainingType.BACHELOR.name,
                    ),
                    doctorat=None,
                ),
            ],
            links={
                'create_training_choice': {'error': 'My error message'},
            },
        )
        url = reverse('admission:list')
        response = self.client.get(url)
        self.assertFalse(response.context['can_create_proposition'])

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_supervised(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_supervised_propositions.return_value = [
            Mock(
                uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                links={'retrieve_project': {'url': 'access granted'}},
                erreurs=[],
            ),
            Mock(uuid='b3729603-c991-489f-8d8d-1d3a11b64dad', links={}, erreurs=[]),
        ]
        url = reverse('admission:supervised-list')
        response = self.client.get(url)
        detail_url = resolve_url('admission:doctorate:project', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        self.assertContains(response, detail_url)
