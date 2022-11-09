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
from django.shortcuts import resolve_url
from rest_framework import status

from admission.contrib.enums.specific_question import Onglets
from admission.tests.views.test_training_choice import AdmissionTrainingChoiceFormViewTestCase


class GeneralEducationSpecificQuestionDetailViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
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
            response.context['form'].initial,
            {
                'specific_question_answers': self.general_proposition.reponses_questions_specifiques,
            },
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={
                'specific_question_answers_1': 'My updated answer',
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_general_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_command={
                'specific_question_answers': {
                    self.first_question_uuid: 'My updated answer',
                },
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
            response.context['form'].initial,
            {
                'specific_question_answers': self.continuing_proposition.reponses_questions_specifiques,
            },
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={
                'specific_question_answers_1': 'My updated answer',
            },
        )

        self.assertRedirects(response, expected_url=self.detail_url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_command={
                'specific_question_answers': {
                    self.first_question_uuid: 'My updated answer',
                },
            },
            **self.default_kwargs,
        )
