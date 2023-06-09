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
from unittest.mock import ANY, MagicMock, patch

import mock
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext
from osis_admission_sdk.model.document_specific_question import DocumentSpecificQuestion

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    TrainingType,
    CleConfigurationItemFormulaire,
    TypeItemFormulaire,
)
from admission.contrib.enums.projet import ChoixStatutPropositionGenerale
from admission.contrib.forms import PDF_MIME_TYPE, JPEG_MIME_TYPE
from base.tests.factories.person import PersonFactory


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
            links={'pay_after_submission': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={},
        )

        cls.url = resolve_url('admission:general-education:payment', pk=cls.proposition.uuid)

        cls.default_kwargs = {
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

        self.addCleanup(propositions_api_patcher.stop)

        self.client.force_login(self.person.user)

    def test_display_payment_form(self):
        # The user doesn't have the permission to pay
        with mock.patch.object(self.proposition, 'links', {}):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.reset_mock()

        # The user have the permission to pay after the submission
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'pay_after_submission': {'url': 'ok'},
            },
        ):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                uuid=self.proposition.uuid,
                **self.default_kwargs,
            )

        self.mock_proposition_api.reset_mock()

        # The user have the permission to pay after a manager request
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'pay_after_request': {'url': 'ok'},
            },
        ):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
                uuid=self.proposition.uuid,
                **self.default_kwargs,
            )

    def test_submit_payment_form_with_invalid_payment(self):
        response = self.client.post(self.url, data={'invalid-payment': ''})

        # Check the response
        self.assertEqual(response.status_code, 200)

        self.assertEqual(str(list(response.context['messages'])[0]), gettext('An error occurred during your payment.'))

    def test_submit_payment_form_with_invalid_request(self):
        response = self.client.post(self.url, data={})

        # Check the response
        self.assertEqual(response.status_code, 400)

    def test_submit_payment_form_with_invalid_permission_configuration(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'pay_after_submission': {'url': 'ok'},
                'pay_after_request': {'url': 'ok'},
            },
        ):
            with self.assertRaises(ImproperlyConfigured):
                self.client.post(self.url, data={'valid-payment': ''})

    def test_submit_payment_form_with_valid_payment_after_submission(self):
        response = self.client.post(self.url, data={'valid-payment': ''})

        # Check the response
        self.assertRedirects(
            response,
            resolve_url(
                'admission:general-education',
                pk=self.proposition.uuid,
            ),
            target_status_code=302,
        )

        self.assertTrue(self.client.session.get('submitted'))

        # Check API calls
        self.mock_proposition_api.return_value.pay_application_fees_after_submission.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

    def test_submit_payment_form_with_valid_payment_after_request(self):
        with mock.patch.object(
            self.proposition,
            'links',
            {
                'pay_after_request': {'url': 'ok'},
            },
        ):
            response = self.client.post(self.url, data={'valid-payment': ''})

            # Check the response
            self.assertRedirects(
                response,
                resolve_url(
                    'admission:general-education',
                    pk=self.proposition.uuid,
                ),
                target_status_code=302,
            )

            # Check API calls
            self.mock_proposition_api.return_value.pay_application_fees_after_request.assert_called_with(
                uuid=self.proposition.uuid,
                **self.default_kwargs,
            )
