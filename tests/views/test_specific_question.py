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
from datetime import datetime
from unittest.mock import patch

from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums.specific_question import Onglets
from admission.contrib.forms import PDF_MIME_TYPE
from admission.tests.views.test_training_choice import AdmissionTrainingChoiceFormViewTestCase


class GeneralEducationSpecificQuestionDetailViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    def setUp(self):
        super().setUp()
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = (
            self.bachelor_proposition
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.side_effect = self.get_specific_questions
        self.addCleanup(propositions_api_patcher.stop)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:general-education:specific-questions', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.assert_called_with(
            uuid=self.proposition_uuid,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.general_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)

    def test_get_page_with_reorientation(self):
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': datetime(2022, 12, 30, 23, 59),
            'modification_pool_end_date': None,
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Reorientation"))

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE})
    def test_get_page_with_modification(self, remote_metadata, remote_token):
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'is_belgian_bachelor': True,
            'is_external_modification': True,
            'registration_change_form': ['uuid'],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, '30/03/2023 23:59')

    def test_get_page_with_residency(self):
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'is_non_resident': None,
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Enrollment in a bachelor with quota"))


class ContinuingEducationSpecificQuestionDetailViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:specific-questions', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.list_continuing_specific_questions.assert_called_with(
            uuid=self.proposition_uuid,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.continuing_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)


class GeneralEducationSpecificQuestionFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:general-education:update:specific-questions', pk=cls.proposition_uuid)
        cls.detail_url = resolve_url('admission:general-education:specific-questions', pk=cls.proposition_uuid)

    def setUp(self):
        super().setUp()
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = (
            self.bachelor_proposition
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.side_effect = self.get_specific_questions
        self.addCleanup(propositions_api_patcher.stop)

        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': None,
        }

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.assert_called_with(
            uuid=self.proposition_uuid,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.general_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)
        self.assertEqual(
            response.context['forms'][0].initial,
            {'specific_question_answers': self.general_proposition.reponses_questions_specifiques},
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={'specific_questions-specific_question_answers_1': 'My updated answer'},
        )

        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_general_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_command={
                'specific_question_answers': {self.first_question_uuid: 'My updated answer'},
            },
            **self.default_kwargs,
        )

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE})
    def test_with_reorientation(self, *__):
        self.mock_proposition_api.return_value.list_doctorate_specific_questions.return_value = []
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': datetime(2022, 12, 30, 23, 59),
            'modification_pool_end_date': None,
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Reorientation"))
        self.assertContains(response, '30/12/2022 23:59')

        response = self.client.post(self.url, data={'': ''})
        self.assertIn('is_belgian_bachelor', response.context['forms'][1].errors)

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': True})
        self.assertIn('is_external_reorientation', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof': [],
        }
        response = self.client.post(self.url, data=data)
        self.assertIn('regular_registration_proof', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': True,
                'regular_registration_proof': ['uuid'],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': False,
                'is_external_reorientation': False,
                'regular_registration_proof': [],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': False,
            'pool_questions-regular_registration_proof_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': False,
                'regular_registration_proof': [],
            },
            **self.default_kwargs,
        )

    @patch('osis_document.api.utils.get_remote_token', return_value='foobar')
    @patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE})
    def test_with_modification(self, *__):
        self.mock_proposition_api.return_value.list_doctorate_specific_questions.return_value = []
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'is_belgian_bachelor': None,
            'is_external_modification': None,
            'registration_change_form': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("Registration change"))
        self.assertContains(response, '30/03/2023 23:59')

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': 'Foo'})
        self.assertIn('is_belgian_bachelor', response.context['forms'][1].errors)

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': True})
        self.assertIn('is_external_modification', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form': [],
        }
        response = self.client.post(self.url, data)
        self.assertIn('registration_change_form', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_modification': True,
                'registration_change_form': ['uuid'],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': False,
                'is_external_modification': False,
                'registration_change_form': [],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': False,
            'pool_questions-registration_change_form_0': 'uuid',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_modification': False,
                'registration_change_form': [],
            },
            **self.default_kwargs,
        )


class ContinuingEducationSpecificQuestionFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:update:specific-questions', pk=cls.proposition_uuid)
        cls.detail_url = resolve_url('admission:continuing-education:specific-questions', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.list_continuing_specific_questions.assert_called_with(
            uuid=self.proposition_uuid,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            **self.default_kwargs,
        )
        self.assertEqual(response.context['admission'].uuid, self.continuing_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)
        self.assertEqual(
            response.context['forms'][0].initial,
            {'specific_question_answers': self.continuing_proposition.reponses_questions_specifiques},
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={'specific_questions-specific_question_answers_1': 'My updated answer'},
        )

        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_command={
                'specific_question_answers': {self.first_question_uuid: 'My updated answer'},
            },
            **self.default_kwargs,
        )
