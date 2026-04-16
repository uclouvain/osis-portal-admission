# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import ANY

from django.shortcuts import resolve_url
from django.utils.translation import gettext

from admission.contrib.enums import (
    TrainingType,
)
from admission.tests.views.training_choice import (
    AdmissionTrainingChoiceFormViewTestCase,
)
from base.tests.factories.person import PersonFactory


class ReEnrolmentViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:re-enrolment')
        cls.create_url = resolve_url('admission:create:training-choice')
        cls.list_url = resolve_url('admission:list')
        cls.person = PersonFactory()
        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }
        cls.message_on_failure = gettext('An error occured when creating the application.')
        cls.message_on_success = gettext('Your data have been saved')

    def test_form_submitting_missing_data(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': '',
                'training_acronym': '',
                'training_year': '',
            },
            follow=True,
        )

        self.assertRedirects(response=response, expected_url=self.list_url)

        messages = [m.message for m in response.context['messages']]
        self.assertIn(self.message_on_failure, messages)

    def test_form_submitting_continuing_training(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TrainingType.CERTIFICATE_OF_SUCCESS.name,
                'training_acronym': 'FC1',
                'training_year': 2025,
            },
            follow=True,
        )

        self.assertRedirects(response=response, expected_url=self.create_url)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

    def test_form_submitting_doctorate_training(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TrainingType.PHD.name,
                'training_acronym': 'FD1',
                'training_year': 2025,
            },
            follow=True,
        )

        self.assertRedirects(response=response, expected_url=self.create_url)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 0)

    def test_form_submitting_general_training(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TrainingType.MASTER_M1.name,
                'training_acronym': 'FG1',
                'training_year': 2025,
            },
            follow=True,
        )

        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:training-choice', pk=self.proposition_uuid),
        )

        self.mock_proposition_api.return_value.create_general_training_choice.assert_called_with(
            initier_proposition_generale_command={
                'sigle_formation': 'FG1',
                'annee_formation': 2025,
                'matricule_candidat': self.person.global_id,
            },
            **self.default_kwargs,
        )

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, self.message_on_success)

        self.mock_proposition_api.return_value.create_general_training_choice.reset_mock()
