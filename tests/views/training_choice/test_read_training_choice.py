# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock

from django.shortcuts import resolve_url

from admission.tests.views.training_choice import (
    AdmissionTrainingChoiceFormViewTestCase,
)


class GeneralAdmissionReadTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:general-education:training-choice', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "osis-document.umd.min.js")
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.general_proposition.uuid)


class ContinuingAdmissionReadTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:training-choice', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.continuing_proposition.uuid)

        # A message is displayed for the HUE candidates
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        mock_proposition = self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value
        mock_proposition.pays_nationalite_ue_candidat = None

        response = self.client.get(self.url)
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        mock_proposition.pays_nationalite_ue_candidat = False
        response = self.client.get(self.url)
        self.assertIn('Les programmes certifiants et courts', response.rendered_content)


class DoctorateAdmissionReadTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:doctorate:training-choice', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.doctorate_proposition.uuid)

    def test_get_page_from_doctorate_management(self):
        self.client.force_login(self.person.user)

        url = resolve_url('gestion_doctorat:doctorate:training-choice', pk=self.proposition_uuid)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.side_effect = None
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value = self.doctorate_proposition

        with mock.patch.object(self.doctorate_proposition, 'links', {'retrieve_doctorate_management': {'url': 'ok'}}):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
