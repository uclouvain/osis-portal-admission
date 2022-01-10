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
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums.actor import ActorType
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import ApiBusinessException, MultipleApiBusinessException
from osis_admission_sdk import ApiException


class SupervisionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)
        self.url = resolve_url("admission:doctorate-update:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)

        self.mock_api.return_value.retrieve_proposition.return_value = Mock(
            links={
                'request_signatures': {
                    'url': 'foobar',
                    'method': 'POST',
                }
            },
        )
        self.mock_api.return_value.retrieve_supervision.return_value = Mock(
            signatures_promoteurs=[Mock(promoteur=Mock(
                matricule="0123456978",
                prenom="Marie-Odile",
                nom="Troufignon",
            ))],
            signatures_membres_ca=[],
        )

    def test_should_detail_supervision_member(self):
        url = resolve_url("admission:doctorate-detail:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url, follow=True)
        self.assertContains(response, "Troufignon")
        self.mock_api.return_value.retrieve_supervision.assert_called()

    def test_should_add_supervision_member(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.url, {
            'type': ActorType.CA_MEMBER.name,
            'tutor': "0123456978",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('person', response.context['form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        response = self.client.post(self.url, {
            'type': ActorType.PROMOTER.name,
            'person': "0123456978",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tutor', response.context['form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        response = self.client.post(self.url, {
            'type': ActorType.PROMOTER.name,
            'tutor': "0123456978",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_api.return_value.add_member.assert_called()

    def test_should_remove_supervision_member(self):
        url = resolve_url(
            "admission:doctorate-detail:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.PROMOTER.name,
            matricule="0123456978",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_api.return_value.remove_member.assert_called()

    def test_should_not_remove_supervision_member_if_not_found(self):
        url = resolve_url(
            "admission:doctorate-detail:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.CA_MEMBER.name,
            matricule="1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = resolve_url(
            "admission:doctorate-detail:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.PROMOTER.name,
            matricule="1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.mock_api.return_value.retrieve_supervision.side_effect = ApiException
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.mock_api.return_value.remove_member.assert_not_called()

    def test_should_not_display_confirmation_if_errors(self):
        url = resolve_url("admission:doctorate-update:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_api.return_value.retrieve_verify_proposition.return_value = [
            {'detail': "Nope"}
        ]
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_api.return_value.retrieve_verify_proposition.assert_called()
        self.assertNotContains(response, _("Are you sure you want to request signatures for this admission?"))
        self.assertContains(response, "Nope")

    def test_should_redirect_to_supervision_without_buttons(self):
        url = resolve_url("admission:doctorate-update:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_api.return_value.retrieve_verify_proposition.return_value = []
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_api.return_value.retrieve_verify_proposition.assert_called()
        self.assertContains(response, _("Are you sure you want to request signatures for this admission?"))

        # Success
        post_url = resolve_url("admission:doctorate-request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(post_url, {})
        self.assertRedirects(response, url)
        self.mock_api.return_value.create_signatures.assert_called()

        # Failure
        post_url = resolve_url("admission:doctorate-request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_api.return_value.create_signatures.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(
                    status_code=42,
                    detail="Something went wrong globally"
                ),
            }
        )
        response = self.client.post(post_url, {}, follow=True)
        self.assertRedirects(response, url)
        self.assertContains(response, _("Please correct the errors first"))
        self.mock_api.return_value.create_signatures.assert_called()
