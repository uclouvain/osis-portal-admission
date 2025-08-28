# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums import ChoixStatutPropositionDoctorale
from admission.contrib.forms import PDF_MIME_TYPE
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CotutelleTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.url = resolve_url("admission:doctorate:update:cotutelle", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_doctorate_proposition.return_value = Mock(
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            links={'update_cotutelle': {'url': 'ok'}},
            erreurs=[],
        )
        self.mock_api.return_value.retrieve_cotutelle.return_value.to_dict.return_value = dict(
            cotutelle=True,
            motivation="Foobar",
            institution="",
            institution_fwb=False,
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
        )

        superior_institute_patcher = patch("admission.contrib.forms.SuperiorInstituteService")
        self.mock_superior_institute_api = superior_institute_patcher.start()
        self.addCleanup(superior_institute_patcher.stop)

        self.mock_superior_institute_api.return_value.get_superior_institute.return_value = {
            'uuid': 'foo',
            'name': 'foo',
            'street': 'foo',
            'street_number': 'foo',
            'zipcode': 'foo',
            'city': 'foo',
        }

    def test_update_no_permission(self):
        self.mock_api.return_value.retrieve_doctorate_proposition.return_value.links = {
            'update_cotutelle': {'error': 'no access'},
        }
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_cotutelle_get(self):
        url = resolve_url("admission:doctorate:cotutelle", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, "Foobar")

    def test_cotutelle_get_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "osis-document.umd.min.js")
        self.assertContains(response, "dependsOn.min.js", count=1)
        self.assertContains(response, "Foobar")
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')
        self.assertEqual(response.context['form'].initial['cotutelle'], 'YES')

    def test_cotutelle_get_form_no_cotutelle(self):
        self.mock_api.return_value.retrieve_cotutelle.return_value.to_dict.return_value = dict(
            cotutelle=False,
            motivation="",
            institution="",
            institution_fwb=None,
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
            institution="",
            institution_fwb=None,
            demande_ouverture=[],
            convention=[],
            autres_documents=[],
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context['form'].initial['cotutelle'], None)

    @patch('osis_document_components.services.get_remote_token', return_value='foobar')
    @patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'size': 1,
        },
    )
    def test_cotutelle_update_with_data(self, *args):
        response = self.client.post(
            self.url,
            {
                'cotutelle': "YES",
                'motivation': "Barbaz",
                'institution': "Bazbar",
                'institution_fwb': False,
                'demande_ouverture_0': "foobar2000",
                'convention': [],
                'autres_documents': [],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.mock_api.return_value.update_cotutelle.assert_called()
        last_call_kwargs = self.mock_api.return_value.update_cotutelle.call_args[1]
        self.assertIn("motivation", last_call_kwargs['definir_cotutelle_command'])
        self.assertEqual(last_call_kwargs['definir_cotutelle_command']['motivation'], "Barbaz")

    def test_cotutelle_update_without_data(self):
        response = self.client.post(self.url, {"cotutelle": "NO", "motivation": "Barbaz"})
        self.assertEqual(response.status_code, 302)
        last_call_kwargs = self.mock_api.return_value.update_cotutelle.call_args[1]
        self.assertEqual(last_call_kwargs['definir_cotutelle_command']['motivation'], "")

    def test_cotutelle_update_missing_data(self):
        response = self.client.post(self.url, {"cotutelle": "YES", "motivation": "Barbaz"})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'institution', _("This field is required."))
