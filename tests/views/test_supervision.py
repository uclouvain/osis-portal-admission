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
from unittest.mock import ANY, Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums.actor import ActorType, ChoixEtatSignature
from admission.contrib.enums.projet import ChoixStatutProposition
from admission.contrib.enums.supervision import DecisionApprovalEnum
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import ApiBusinessException, MultipleApiBusinessException
from osis_admission_sdk import ApiException


class SupervisionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.pk = "3c5cdc60-2537-4a12-a396-64d2e9e34876"

        self.client.force_login(self.person.user)
        self.update_url = resolve_url("admission:doctorate:update:supervision", pk=self.pk)
        self.detail_url = resolve_url("admission:doctorate:supervision", pk=self.pk)
        self.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

        api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_api = api_patcher.start()
        self.addCleanup(api_patcher.stop)
        self.mock_api.return_value.retrieve_proposition.return_value = Mock(
            code_secteur_formation="SSH",
            institut_these='',
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            statut=ChoixStatutProposition.SIGNING_IN_PROGRESS.name,
            links={
                'add_approval': {'error': 'nope'},
                'request_signatures': {'error': 'nope'},
                'add_member': {'error': 'nope'},
            },
        )

        self.mock_api.return_value.retrieve_supervision.return_value.to_dict.return_value = dict(
            signatures_promoteurs=[
                dict(
                    promoteur=dict(
                        matricule="0123456978",
                        prenom="Marie-Odile",
                        nom="Troufignon",
                    ),
                    statut=ChoixEtatSignature.APPROVED.name,
                    commentaire_externe="A public comment to display",
                ),
                dict(
                    promoteur=dict(
                        matricule="9876543210",
                        prenom="John",
                        nom="Doe",
                    ),
                    statut=ChoixEtatSignature.DECLINED.name,
                    commentaire_externe="A public comment to display",
                ),
            ],
            signatures_membres_ca=[
                dict(
                    membre_ca=dict(
                        matricule=self.person.global_id,
                        prenom="Jacques-Eudes",
                        nom="Birlimpette",
                    ),
                    statut=ChoixEtatSignature.INVITED.name,
                ),
            ],
        )

    def test_should_detail_redirect_to_form_when_not_signing(self):
        self.mock_api.return_value.retrieve_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_proposition.return_value.statut = ChoixStatutProposition.IN_PROGRESS.name
        response = self.client.get(self.detail_url)
        # Display the signatures
        self.assertRedirects(response, self.update_url)

    def test_should_detail_supervision_member(self):
        response = self.client.get(self.detail_url)
        # Display the signatures
        self.assertContains(response, "Troufignon")
        self.assertContains(response, ChoixEtatSignature.APPROVED.value)
        self.assertContains(response, "A public comment to display")
        self.assertContains(response, ChoixEtatSignature.DECLINED.value)
        self.mock_api.return_value.retrieve_supervision.assert_called()

    def test_should_add_supervision_member(self):
        self.mock_api.return_value.retrieve_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.update_url, {'type': ActorType.CA_MEMBER.name, 'tutor': "0123456978"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('person', response.context['form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        response = self.client.post(self.update_url, {'type': ActorType.PROMOTER.name, 'person': "0123456978"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tutor', response.context['form'].errors)
        self.mock_api.return_value.add_member.assert_not_called()

        response = self.client.post(self.update_url, {'type': ActorType.PROMOTER.name, 'tutor': "0123456978"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_api.return_value.add_member.assert_called()

    def test_should_remove_supervision_member(self):
        url = resolve_url(
            "admission:doctorate:remove-actor",
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
            "admission:doctorate:remove-actor",
            pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
            type=ActorType.CA_MEMBER.name,
            matricule="1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = resolve_url(
            "admission:doctorate:remove-actor",
            pk=self.pk,
            type=ActorType.PROMOTER.name,
            matricule="1234569780",
        )
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.mock_api.return_value.retrieve_supervision.side_effect = ApiException
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.mock_api.return_value.remove_member.assert_not_called()

    def test_should_approve_proposition(self):
        # All data is provided and the proposition is approved
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.APPROVED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",  # The reason is provided but will not be used
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_api.return_value.approve_proposition.assert_called_with(
            uuid=self.pk,
            approuver_proposition_command={
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'matricule': self.person.global_id,
            },
            **self.default_kwargs,
        )

        self.mock_api.return_value.approve_proposition.reset_mock()

    def test_should_error_when_first_promoter_and_no_institute(self):
        self.mock_api.return_value.retrieve_supervision.return_value.to_dict.return_value = dict(
            signatures_promoteurs=[
                dict(
                    promoteur=dict(
                        matricule="0123456978",
                        prenom="Marie-Odile",
                        nom="Troufignon",
                    ),
                    statut=ChoixEtatSignature.INVITED.name,
                ),
            ],
            signatures_membres_ca=[],
        )
        self.client.force_login(PersonFactory(global_id='0123456978').user)
        response = self.client.post(self.detail_url, {'decision': DecisionApprovalEnum.APPROVED.name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "form", 'institut_these', _('This field is required.'))

    def test_should_reject_proposition(self):
        # All data is provided and the proposition is rejected
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.mock_api.return_value.reject_proposition.assert_called_with(
            uuid=self.pk,
            refuser_proposition_command={
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
                'matricule': self.person.global_id,
            },
            **self.default_kwargs,
        )

        self.mock_api.return_value.reject_proposition.reset_mock()

    def test_should_error_with_no_decision(self):
        # The decision is missing
        response = self.client.post(
            self.detail_url,
            {
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
                'motif_refus': "The reason",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('decision', response.context['form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()

    def test_should_reject_with_error_when_no_motive(self):
        response = self.client.post(
            self.detail_url,
            {
                'decision': DecisionApprovalEnum.DECLINED.name,
                'commentaire_interne': "The internal comment",
                'commentaire_externe': "The public comment",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('motif_refus', response.context['form'].errors)

        self.mock_api.return_value.reject_proposition.assert_not_called()
        self.mock_api.return_value.approve_proposition.assert_not_called()

    def test_update_should_redirect_to_detail_if_no_permission(self):
        response = self.client.get(self.update_url)
        self.assertRedirects(response, self.detail_url)

    def test_should_not_display_confirmation_if_errors(self):
        self.mock_api.return_value.retrieve_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
                'add_member': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_verify_project.return_value = [{'detail': "Nope"}]
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_api.return_value.retrieve_verify_project.assert_called()
        self.assertNotContains(response, _("Are you sure you want to request signatures for this admission?"))
        self.assertContains(response, "Nope")

    def test_should_redirect_to_supervision_without_buttons(self):
        self.mock_api.return_value.retrieve_proposition.return_value.links.update(
            {
                'request_signatures': {'url': 'ok'},
            }
        )
        self.mock_api.return_value.retrieve_verify_project.return_value = []
        response = self.client.get(self.update_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_api.return_value.retrieve_verify_project.assert_called()
        self.assertContains(response, _("Are you sure you want to request signatures for this admission?"))

        # Success
        post_url = resolve_url("admission:doctorate:request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(post_url, {})
        self.assertRedirects(response, self.detail_url)
        self.mock_api.return_value.create_signatures.assert_called()

        # Failure
        post_url = resolve_url("admission:doctorate:request-signatures", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_api.return_value.create_signatures.side_effect = MultipleApiBusinessException(
            exceptions={
                ApiBusinessException(status_code=42, detail="Something went wrong globally"),
            }
        )
        response = self.client.post(post_url, {}, follow=True)
        self.assertRedirects(response, self.update_url)
        self.assertContains(response, _("Please correct the errors first"))
        self.mock_api.return_value.create_signatures.assert_called()

    @patch(
        'osis_document.api.utils.get_remote_metadata',
        return_value={'name': 'myfile', 'mimetype': 'application/pdf'},
    )
    def test_should_approval_by_pdf_redirect_without_errors(self, *args):
        url = resolve_url("admission:doctorate:approve-by-pdf", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(url, {'matricule': "test", 'pdf_0': 'some_file'})
        expected_url = resolve_url("admission:doctorate:supervision", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.assertRedirects(response, expected_url)

    def test_should_approval_by_pdf_redirect_with_errors(self):
        url = resolve_url("admission:doctorate:approve-by-pdf", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(url, {})
        self.assertRedirects(response, self.detail_url)
