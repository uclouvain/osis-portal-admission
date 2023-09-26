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
import datetime
import uuid
from unittest.mock import ANY, MagicMock, patch

import mock
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from rest_framework.status import HTTP_200_OK

from admission.contrib.enums import (
    TrainingType,
)
from admission.contrib.enums.payment import PaymentStatus, PaymentMethod
from admission.contrib.enums.projet import ChoixStatutPropositionGenerale
from base.tests.factories.person import PersonFactory
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class DocumentsFormViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition = MagicMock(
            uuid=str(uuid.uuid4()),
            formation=MagicMock(
                annee=2020,
                intitule='Formation',
                campus='Mons',
                sigle='TR1',
                type=TrainingType.MASTER_M1.name,
            ),
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionGenerale.FRAIS_DOSSIER_EN_ATTENTE.name,
            links={'view_payment': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={},
        )
        cls.payments = {
            'id_p1': MagicMock(
                identifiant_paiement='id_p1',
                statut=PaymentStatus.PAID.name,
                methode=PaymentMethod.BANCONTACT.name,
                montant='200',
                url_checkout='https://dummy_url_id_p1/checkout',
                date_creation=datetime.datetime(2020, 1, 2, 0),
                date_mise_a_jour=datetime.datetime(2020, 1, 2, 1),
                date_expiration=datetime.datetime(2020, 1, 2, 2),
            ),
            'id_p2': MagicMock(
                identifiant_paiement='id_p2',
                statut=PaymentStatus.CANCELED.name,
                methode=PaymentMethod.BANK_TRANSFER.name,
                montant='200',
                url_checkout='https://dummy_url_id_p2/checkout',
                date_creation=datetime.datetime(2020, 1, 1, 0),
                date_mise_a_jour=datetime.datetime(2020, 1, 1, 1),
                date_expiration=datetime.datetime(2020, 1, 1, 2),
            ),
        }
        cls.payments_as_list = list(cls.payments.values())

        cls.url = resolve_url('admission:general-education:payment', pk=cls.proposition.uuid)

        cls.default_kwargs = {
            'uuid': cls.proposition.uuid,
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = self.proposition

        self.mock_proposition_api.return_value.list_application_fees_payments.return_value = self.payments_as_list

        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.return_value = (
            self.payments_as_list[0]
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.return_value = (
            self.payments_as_list[0]
        )

        self.addCleanup(propositions_api_patcher.stop)

        self.client.force_login(self.person.user)

    @staticmethod
    def _raise_already_paid_exception(*args, **kwargs):
        raise MultipleApiBusinessException(exceptions=MagicMock(detail="Already paid"))

    def test_raise_permission_denied_when_no_permission(self):
        with mock.patch.object(self.proposition, 'links', {}):
            response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_display_the_payment_list_if_already_paid_and_cannot_pay_and_no_recent_payment(self):
        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payments'], [self.payments_as_list[0]])
        self.assertEqual(response.context['already_paid'], True)
        self.assertEqual(response.context['can_pay'], False)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_redirect_to_default_proposition_page_if_already_paid_and_cannot_pay_and_recent_payment_after_submission(
        self,
    ):
        session = self.client.session
        session[f'pay_fees_{self.proposition.uuid}'] = 'after_submission:id_p1'
        session.save()

        response = self.client.get(self.url)

        # Check response
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education', pk=self.proposition.uuid),
            fetch_redirect_response=False,
        )

        session = self.client.session
        self.assertEqual(session.get('submitted'), True)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_redirect_to_default_proposition_page_if_already_paid_and_cannot_pay_and_recent_payment_after_request(self):
        session = self.client.session
        session[f'pay_fees_{self.proposition.uuid}'] = 'after_request:id_p1'
        session.save()

        response = self.client.get(self.url)

        # Check response
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education', pk=self.proposition.uuid),
            fetch_redirect_response=False,
        )

        session = self.client.session
        self.assertEqual(session.get('submitted'), None)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_display_the_payment_list_if_already_paid_and_cannot_pay_and_unknown_recent_payment(self):
        session = self.client.session
        session[f'pay_fees_{self.proposition.uuid}'] = 'after_request:id_unknown'
        session.save()

        response = self.client.get(self.url)

        # Check response
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.context['payments'], [self.payments_as_list[0]])
        self.assertEqual(response.context['already_paid'], True)
        self.assertEqual(response.context['can_pay'], False)

        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_display_the_payment_list_if_already_paid_and_can_pay_after_manager_request_and_no_recent_payment(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'view_payment': {'url': 'ok'},
                'pay_after_request': {'url': 'ok'},
            },
        ):
            self.mock_proposition_api.return_value.open_application_fees_payment_after_request.side_effect = (
                self._raise_already_paid_exception
            )

            response = self.client.get(self.url)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['payments'], [self.payments_as_list[0]])
            self.assertEqual(response.context['already_paid'], True)
            self.assertEqual(response.context['can_pay'], True)

            # Check api calls
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()
            self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()

    def test_display_the_payment_list_if_already_paid_and_can_pay_after_submission_and_no_recent_payment(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'view_payment': {'url': 'ok'},
                'pay_after_submission': {'url': 'ok'},
            },
        ):
            self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.side_effect = (
                self._raise_already_paid_exception
            )

            response = self.client.get(self.url)

            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['payments'], [self.payments_as_list[0]])
            self.assertEqual(response.context['already_paid'], True)
            self.assertEqual(response.context['can_pay'], True)

            # Check api calls
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
            self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_redirect_to_checkout_page_if_not_already_paid_and_can_pay_after_submission(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'view_payment': {'url': 'ok'},
                'pay_after_submission': {'url': 'ok'},
            },
        ):
            self.mock_proposition_api.return_value.list_application_fees_payments.return_value = []

            response = self.client.get(self.url)

            # Check response
            self.assertRedirects(
                response=response,
                expected_url=self.payments['id_p1'].url_checkout,
                fetch_redirect_response=False,
            )

            # Check api calls
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_called_with(
                **self.default_kwargs,
            )
            self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()

    def test_redirect_to_checkout_page_if_not_already_paid_and_can_pay_after_manager_request(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'view_payment': {'url': 'ok'},
                'pay_after_request': {'url': 'ok'},
            },
        ):
            self.mock_proposition_api.return_value.list_application_fees_payments.return_value = []

            response = self.client.get(self.url)

            # Check response
            self.assertRedirects(
                response=response,
                expected_url=self.payments['id_p1'].url_checkout,
                fetch_redirect_response=False,
            )

            # Check api calls
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
                **self.default_kwargs,
            )

            self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_called_with(
                **self.default_kwargs,
            )
            self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()

    def test_display_the_payment_list_if_already_paid_and_from_mollie(self):
        response = self.client.get(self.url + '?from_mollie=1')

        # Check response
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.context['payments'], [self.payments_as_list[0]])
        self.assertEqual(response.context['already_paid'], True)
        self.assertEqual(response.context['can_pay'], False)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()

    def test_display_the_payment_list_if_not_already_paid_and_from_mollie(self):
        self.mock_proposition_api.return_value.list_application_fees_payments.return_value = []

        response = self.client.get(self.url + '?from_mollie=1')

        # Check response
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.context['payments'], [])
        self.assertEqual(response.context['already_paid'], False)
        self.assertEqual(response.context['can_pay'], False)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_application_fees_payments.assert_called_with(
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.open_application_fees_payment_after_request.assert_not_called()
        self.mock_proposition_api.return_value.open_application_fees_payment_after_submission.assert_not_called()
