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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.person import PersonFactory


class ListTestCase(TestCase):
    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_empty(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_propositions.return_value = {
            'doctorate_propositions': [],
            'continuing_education_propositions': [],
            'general_education_propositions': [],
            'links': {
                'create_doctorate_proposition': {'url': 'access granted'},
                'create_general_proposition': {'url': 'access granted'},
                'create_continuing_proposition': {'url': 'access granted'},
            },
        }
        url = reverse('admission:list')
        response = self.client.get(url)
        self.assertTrue(response.context['can_create_proposition'])
        create_url = resolve_url('admission:create')
        self.assertContains(response, create_url)

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_propositions.return_value = {
            'doctorate_propositions': [
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_proposition': {'url': 'access granted'}},
                    erreurs=[],
                ),
                Mock(uuid='b3729603-c991-489f-8d8d-1d3a11b64dad', links={}, erreurs=[]),
            ],
            'continuing_education_propositions': [
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                ),
            ],
            'general_education_propositions': [
                Mock(
                    uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                    links={'retrieve_training_choice': {'url': 'access granted'}},
                    erreurs=[],
                ),
            ],
            'links': {
                'create_doctorate_proposition': {'errors': ['error']},
                'create_general_proposition': {'errors': ['error']},
                'create_continuing_proposition': {'errors': ['error']},
            },
        }
        url = reverse('admission:list')
        response = self.client.get(url)
        self.assertFalse(response.context['can_create_proposition'])

        doctorate_proposition_detail_url = resolve_url(
            'admission:doctorate:project',
            pk='3c5cdc60-2537-4a12-a396-64d2e9e34876',
        )
        continuing_proposition_detail_url = resolve_url(
            'admission:continuing-education:training-choice',
            pk='3c5cdc60-2537-4a12-a396-64d2e9e34876',
        )
        general_proposition_detail_url = resolve_url(
            'admission:general-education:training-choice',
            pk='3c5cdc60-2537-4a12-a396-64d2e9e34876',
        )

        self.assertContains(response, doctorate_proposition_detail_url)
        self.assertContains(response, continuing_proposition_detail_url)
        self.assertContains(response, general_proposition_detail_url)

    @patch('osis_admission_sdk.api.propositions_api.PropositionsApi')
    def test_list_supervised(self, api, *args):
        self.client.force_login(PersonFactory().user)
        api.return_value.list_supervised_propositions.return_value = [
            Mock(
                uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
                links={'retrieve_proposition': {'url': 'access granted'}},
                erreurs=[],
            ),
            Mock(uuid='b3729603-c991-489f-8d8d-1d3a11b64dad', links={}, erreurs=[]),
        ]
        url = reverse('admission:supervised-list')
        response = self.client.get(url)
        detail_url = resolve_url('admission:doctorate:project', pk='3c5cdc60-2537-4a12-a396-64d2e9e34876')
        self.assertContains(response, detail_url)
