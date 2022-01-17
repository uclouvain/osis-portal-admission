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
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CotutelleTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url("admission:doctorate-update:cotutelle", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_cotutelle.return_value.to_dict.return_value = dict(
            cotutelle=True,
            motivation="Foobar",
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
        )

    def test_cotutelle_get(self):
        url = resolve_url("admission:doctorate-detail:cotutelle", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertContains(response, "Foobar")

    def test_cotutelle_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Foobar")
        self.assertEqual(response.context['form'].initial['cotutelle'], 'YES')

    def test_cotutelle_get_form_no_cotutelle(self):
        self.mock_api.return_value.retrieve_cotutelle.return_value.to_dict.return_value = dict(
            cotutelle=False,
            motivation="",
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['cotutelle'], 'NO')

    def test_cotutelle_get_form_cotutelle_undefined(self):
        self.mock_api.return_value.retrieve_cotutelle.return_value.to_dict.return_value = dict(
            cotutelle=None,
            motivation="",
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['cotutelle'], None)

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
    def test_cotutelle_update_with_data(self, *args):
        response = self.client.post(self.url, {
            'cotutelle': "YES",
            'motivation': "Barbaz",
            'institution': "Bazbar",
            'demande_ouverture_0': "foobar2000",
            'convention': [],
            'autres_documents': [],
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_api.return_value.update_cotutelle.assert_called()
        last_call_kwargs = self.mock_api.return_value.update_cotutelle.call_args[1]
        self.assertIn("motivation", last_call_kwargs['definir_cotutelle_command'])
        self.assertEqual(last_call_kwargs['definir_cotutelle_command']['motivation'], "Barbaz")

    def test_cotutelle_update_without_data(self):
        response = self.client.post(self.url, {
            "cotutelle": "NO",
            "motivation": "Barbaz",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        last_call_kwargs = self.mock_api.return_value.update_cotutelle.call_args[1]
        self.assertEqual(last_call_kwargs['definir_cotutelle_command']['motivation'], "")

    def test_cotutelle_update_missing_data(self):
        response = self.client.post(self.url, {
            "cotutelle": "YES",
            "motivation": "Barbaz",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'institution', _("This field is required."))
