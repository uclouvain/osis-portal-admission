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
from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from osis_admission_sdk.model.modifier_questions_specifiques_formation_continue_command import (
    ModifierQuestionsSpecifiquesFormationContinueCommand,
)
from osis_admission_sdk.model.modifier_questions_specifiques_formation_generale_command import (
    ModifierQuestionsSpecifiquesFormationGeneraleCommand,
)
from osis_admission_sdk.model.poste_diplomatique_dto_nested import (
    PosteDiplomatiqueDTONested,
)

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.additional_information import (
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.forms import EMPTY_CHOICE, PDF_MIME_TYPE
from admission.tests.views.training_choice import (
    AdmissionTrainingChoiceFormViewTestCase,
)


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

        self.assertEqual(response.status_code, 200)
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
            'reorientation_pool_academic_year': 2022,
            'modification_pool_academic_year': None,
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
            'reorientation_form': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Course change"))

    @patch('osis_document_components.services.get_remote_token', return_value='foobar')
    @patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'size': 1,
        },
    )
    def test_get_page_with_modification(self, remote_metadata, remote_token):
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': 2023,
            'is_belgian_bachelor': True,
            'is_external_modification': True,
            'registration_change_form': ['uuid'],
            'regular_registration_proof_for_registration_change': ['uuid-2'],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '30/03/2023 23:59')

    def test_get_page_with_residency(self):
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': 2023,
            'is_non_resident': None,
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Enrolment in limited enrolment bachelor's course"))

    def test_get_page_with_residency_when_forbidden(self):
        # Not forbidden
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': 2023,
            'is_non_resident': True,
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'This enrolment is forbidden.')

        # Forbidden
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': 2023,
            'is_non_resident': True,
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This enrolment is forbidden.')


class ContinuingEducationSpecificQuestionDetailViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:specific-questions', pk=cls.proposition_uuid)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
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
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': None,
        }

    def test_forbidden_access(self):
        with patch.object(self.bachelor_proposition, 'links', {'update_specific_question': {'error': 'a'}}):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 403)

            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 403)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.list_general_specific_questions.assert_called_with(
            uuid=self.proposition_uuid,
            tab=Onglets.INFORMATIONS_ADDITIONNELLES.name,
            **self.default_kwargs,
        )

        self.assertEqual(response.context['admission'].uuid, self.bachelor_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)
        main_form = response.context['forms'][0]
        self.assertEqual(
            main_form.initial,
            {
                'reponses_questions_specifiques': self.bachelor_proposition.reponses_questions_specifiques,
                'documents_additionnels': self.bachelor_proposition.documents_additionnels,
                'poste_diplomatique': None,
            },
        )
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)
        self.assertFalse(main_form.fields['poste_diplomatique'].required)

    def test_get_page_with_visa_question(self):
        # No identification -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = None

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification but no nationality or residence -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='',
            pays_nationalite_europeen=None,
            pays_residence='',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification and UE nationality and foreign residence -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='FR',
            pays_nationalite_europeen=True,
            pays_residence='FR',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification and UE+5 nationality and foreign residence -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='CH',
            pays_nationalite_europeen=False,
            pays_residence='FR',
        )

        response = self.client.get(self.url)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification and not UE+5 nationality but no residence -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='US',
            pays_nationalite_europeen=False,
            pays_residence='',
        )

        response = self.client.get(self.url)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification and not UE+5 nationality and residence in Belgium -> no visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='US',
            pays_nationalite_europeen=False,
            pays_residence='BE',
        )

        response = self.client.get(self.url)
        main_form = response.context['forms'][0]
        self.assertTrue(main_form.fields['poste_diplomatique'].disabled)

        # With identification and not UE+5 nationality and residence not in Belgium -> visa
        # > Without initial visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='US',
            pays_nationalite_europeen=False,
            pays_residence='FR',
        )

        response = self.client.get(self.url)
        main_form = response.context['forms'][0]
        self.assertFalse(main_form.fields['poste_diplomatique'].disabled)
        self.assertTrue(main_form.fields['poste_diplomatique'].required)
        self.assertEqual(main_form.fields['poste_diplomatique'].choices, EMPTY_CHOICE)

        # > With initial visa
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='US',
            pays_nationalite_europeen=False,
            pays_residence='FR',
        )
        proposition = self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value
        proposition.poste_diplomatique = PosteDiplomatiqueDTONested._from_openapi_data(
            code=self.first_diplomatic_post.code,
            nom_francais='',
            nom_anglais='',
            adresse_email='',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.mock_diplomatic_post_api.return_value.retrieve_diplomatic_post.assert_called_with(
            code=self.first_diplomatic_post.code,
            **self.default_kwargs,
        )

        main_form = response.context['forms'][0]
        self.assertFalse(main_form.fields['poste_diplomatique'].disabled)
        self.assertEqual(
            main_form.fields['poste_diplomatique'].choices,
            EMPTY_CHOICE
            + (
                (
                    self.first_diplomatic_post.code,
                    self.first_diplomatic_post.name_fr,
                ),
            ),
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-documents_additionnels_0': 'uuid-doc',
                'specific_questions-poste_diplomatique': self.first_diplomatic_post.code,
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_general_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_generale_command=(
                ModifierQuestionsSpecifiquesFormationGeneraleCommand(
                    **{
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                        'documents_additionnels': ['uuid-doc'],
                        'poste_diplomatique': None,  # Visa not requested
                    }
                )
            ),
            **self.default_kwargs,
        )

    def test_post_page_with_visa(self):
        self.mock_proposition_api.return_value.retrieve_general_identification.return_value = MagicMock(
            pays_nationalite='US',
            pays_nationalite_europeen=False,
            pays_residence='FR',
        )

        # The visa is required but not specified
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-poste_diplomatique': '',
            },
        )

        self.assertEqual(response.status_code, 200)

        main_form = response.context['forms'][0]

        self.assertFalse(main_form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, main_form.errors.get('poste_diplomatique', []))

        # The visa is required and specified
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-poste_diplomatique': self.second_diplomatic_post.code,
            },
        )

        self.assertRedirects(response, self.url)

        self.mock_proposition_api.return_value.update_general_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_generale_command=(
                ModifierQuestionsSpecifiquesFormationGeneraleCommand(
                    **{
                        'documents_additionnels': [],
                        'poste_diplomatique': self.second_diplomatic_post.code,
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                    }
                )
            ),
            **self.default_kwargs,
        )

        self.mock_diplomatic_post_api.return_value.retrieve_diplomatic_post.assert_called_with(
            code=self.second_diplomatic_post.code,
            **self.default_kwargs,
        )

    @patch('osis_document_components.services.get_remote_token', return_value='foobar')
    @patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'size': 1,
        },
    )
    def test_with_reorientation(self, *__):
        self.mock_proposition_api.return_value.list_doctorate_specific_questions.return_value = []
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': datetime(2022, 12, 30, 23, 59),
            'modification_pool_end_date': None,
            'reorientation_pool_academic_year': 2022,
            'modification_pool_academic_year': None,
            'is_belgian_bachelor': None,
            'is_external_reorientation': None,
            'regular_registration_proof': [],
            'reorientation_form': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Course change"))
        self.assertContains(response, '30/12/2022 23:59')

        response = self.client.post(self.url, data={'': ''})
        self.assertIn('is_belgian_bachelor', response.context['forms'][1].errors)

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': True})
        self.assertIn('is_external_reorientation', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof': [],
            'pool_questions-reorientation_form': [],
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, self.url)

        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': True,
                'reorientation_form': [],
                'regular_registration_proof': [],
            },
            **self.default_kwargs,
        )
        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
            'pool_questions-reorientation_form_0': 'uuid2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)

        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': True,
                'regular_registration_proof': ['uuid'],
                'reorientation_form': ['uuid2'],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
            'pool_questions-reorientation_form_0': 'uuid2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': False,
                'is_external_reorientation': False,
                'regular_registration_proof': [],
                'reorientation_form': [],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': False,
            'pool_questions-regular_registration_proof_0': 'uuid',
            'pool_questions-reorientation_form_0': 'uuid2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': False,
                'regular_registration_proof': [],
                'reorientation_form': [],
            },
            **self.default_kwargs,
        )

    @patch('osis_document_components.services.get_remote_token', return_value='foobar')
    @patch(
        'osis_document_components.services.get_remote_metadata',
        return_value={
            'name': 'myfile',
            'mimetype': PDF_MIME_TYPE,
            'size': 1,
        },
    )
    def test_with_modification(self, *__):
        self.mock_proposition_api.return_value.list_doctorate_specific_questions.return_value = []
        self.mock_proposition_api.return_value.retrieve_pool_questions.return_value.to_dict.return_value = {
            'reorientation_pool_end_date': None,
            'modification_pool_end_date': datetime(2023, 3, 30, 23, 59),
            'reorientation_pool_academic_year': None,
            'modification_pool_academic_year': 2023,
            'is_belgian_bachelor': None,
            'is_external_modification': None,
            'registration_change_form': [],
            'regular_registration_proof_for_registration_change': [],
        }
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Change of enrolment"))
        self.assertContains(response, '30/03/2023 23:59')
        self.assertContains(response, '2023-2024')

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': 'Foo'})
        self.assertIn('is_belgian_bachelor', response.context['forms'][1].errors)

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': True})
        self.assertIn('is_external_modification', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form': [],
            'pool_questions-regular_registration_proof_for_registration_change': [],
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_modification': True,
                'registration_change_form': [],
                'regular_registration_proof_for_registration_change': [],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
            'pool_questions-regular_registration_proof_for_registration_change_0': 'uuid-2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_modification': True,
                'registration_change_form': ['uuid'],
                'regular_registration_proof_for_registration_change': ['uuid-2'],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
            'pool_questions-regular_registration_proof_for_registration_change_0': 'uuid-2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': False,
                'is_external_modification': False,
                'registration_change_form': [],
                'regular_registration_proof_for_registration_change': [],
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': False,
            'pool_questions-registration_change_form_0': 'uuid',
            'pool_questions-regular_registration_proof_for_registration_change_0': 'uuid-2',
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_modification': False,
                'registration_change_form': [],
                'regular_registration_proof_for_registration_change': [],
            },
            **self.default_kwargs,
        )


class ContinuingEducationSpecificQuestionFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:update:specific-questions', pk=cls.proposition_uuid)

    def test_forbidden_access(self):
        with patch.object(self.continuing_proposition, 'links', {'update_specific_question': {'error': 'a'}}):
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 403)

            response = self.client.post(self.url)

            self.assertEqual(response.status_code, 403)

    def test_get_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
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
        initial_data = response.context['forms'][0].initial
        self.assertEqual(
            initial_data.get('reponses_questions_specifiques'),
            self.continuing_proposition.reponses_questions_specifiques,
        )
        self.assertEqual(initial_data.get('inscription_a_titre'), 'PROFESSIONNEL')
        self.assertEqual(initial_data.get('nom_siege_social'), 'UCL')
        self.assertEqual(initial_data.get('numero_unique_entreprise'), '1')
        self.assertEqual(initial_data.get('numero_tva_entreprise'), '1A')
        self.assertEqual(initial_data.get('adresse_mail_professionnelle'), 'john.doe@example.be'),
        self.assertEqual(initial_data.get('type_adresse_facturation'), 'AUTRE')
        self.assertEqual(initial_data.get('adresse_facturation_destinataire'), 'Mr Doe')
        self.assertEqual(initial_data.get('street'), 'Rue des Pins')
        self.assertEqual(initial_data.get('street_number'), '10')
        self.assertEqual(initial_data.get('postal_box'), 'B1')
        self.assertEqual(initial_data.get('postal_code'), '1348')
        self.assertEqual(initial_data.get('city'), 'Louvain-La-Neuve')
        self.assertEqual(initial_data.get('country'), 'BE')

    def test_get_page_without_billing_address(self):
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value.to_dict = (
            lambda **kwargs: {
                **self.continuing_proposition_dict,
                'type_adresse_facturation': 'RESIDENTIEL',
                'adresse_facturation': None,
            }
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        initial_data = response.context['forms'][0].initial
        self.assertEqual(
            initial_data.get('reponses_questions_specifiques'),
            self.continuing_proposition.reponses_questions_specifiques,
        )
        self.assertEqual(initial_data.get('inscription_a_titre'), 'PROFESSIONNEL')
        self.assertEqual(initial_data.get('nom_siege_social'), 'UCL')
        self.assertEqual(initial_data.get('numero_unique_entreprise'), '1')
        self.assertEqual(initial_data.get('numero_tva_entreprise'), '1A')
        self.assertEqual(initial_data.get('adresse_mail_professionnelle'), 'john.doe@example.be'),
        self.assertEqual(initial_data.get('type_adresse_facturation'), 'RESIDENTIEL')

    def test_post_page_enrolment_with_residence_permit(self):
        mock_retrieve_doctorate_proposition = (
            self.mock_proposition_api.return_value.retrieve_continuing_education_proposition
        )
        mock_retrieve_doctorate_proposition.return_value.pays_nationalite_ue_candidat = True
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                'specific_questions-copie_titre_sejour_0': ['file-token'],
                'specific_questions-documents_additionnels_0': ['file-token1'],
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=ANY,
            **self.default_kwargs,
        )

        mock_retrieve_doctorate_proposition.return_value.pays_nationalite_ue_candidat = False
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                'specific_questions-copie_titre_sejour_0': ['file-token'],
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=ANY,
            **self.default_kwargs,
        )

    def test_post_page_enrolment_as_private(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                # Excess fields that will be ignored
                'specific_questions-nom_siege_social': 'UCLouvain',
                'specific_questions-numero_unique_entreprise': '1234',
                'specific_questions-numero_tva_entreprise': '1234A',
                'specific_questions-adresse_mail_professionnelle': 'jane.doe@example.be',
                'specific_questions-type_adresse_facturation': ChoixTypeAdresseFacturation.RESIDENTIEL.name,
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=(
                ModifierQuestionsSpecifiquesFormationContinueCommand(
                    **{
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                        'inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                        'copie_titre_sejour': [],
                        'documents_additionnels': [],
                    }
                )
            ),
            **self.default_kwargs,
        )

    def test_post_page_enrolment_as_professional(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'specific_questions-nom_siege_social': 'UCLouvain',
                'specific_questions-numero_unique_entreprise': '1234',
                'specific_questions-numero_tva_entreprise': '1234A',
                'specific_questions-adresse_mail_professionnelle': 'jane.doe@example.be',
                'specific_questions-type_adresse_facturation': ChoixTypeAdresseFacturation.RESIDENTIEL.name,
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=(
                ModifierQuestionsSpecifiquesFormationContinueCommand(
                    **{
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                        'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                        'nom_siege_social': 'UCLouvain',
                        'numero_unique_entreprise': '1234',
                        'numero_tva_entreprise': '1234A',
                        'adresse_mail_professionnelle': 'jane.doe@example.be',
                        'type_adresse_facturation': ChoixTypeAdresseFacturation.RESIDENTIEL.name,
                        'copie_titre_sejour': [],
                        'documents_additionnels': [],
                    }
                )
            ),
            **self.default_kwargs,
        )

    def test_post_page_enrolment_as_professional_with_missing_fields(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_not_called()
        form = response.context['form']
        self.assertFalse(form.is_valid())
        for field in [
            'nom_siege_social',
            'numero_unique_entreprise',
            'numero_tva_entreprise',
            'adresse_mail_professionnelle',
            'type_adresse_facturation',
        ]:
            self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get(field, []))

    def test_post_page_enrolment_as_professional_with_custom_foreign_billing_address(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'specific_questions-nom_siege_social': 'UCLouvain',
                'specific_questions-numero_unique_entreprise': '1234',
                'specific_questions-numero_tva_entreprise': '1234A',
                'specific_questions-adresse_mail_professionnelle': 'jane.doe@example.be',
                'specific_questions-type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                'specific_questions-adresse_facturation_destinataire': 'Jane Doe',
                'specific_questions-street': 'Rue du moulin',
                'specific_questions-street_number': '1',
                'specific_questions-postal_code': '44000',
                'specific_questions-city': 'Nantes',
                'specific_questions-country': 'FR',
                'specific_questions-postal_box': 'PB1',
                'specific_questions-place': 'Avant',
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=(
                ModifierQuestionsSpecifiquesFormationContinueCommand(
                    **{
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                        'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                        'nom_siege_social': 'UCLouvain',
                        'numero_unique_entreprise': '1234',
                        'numero_tva_entreprise': '1234A',
                        'adresse_mail_professionnelle': 'jane.doe@example.be',
                        'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                        'adresse_facturation_rue': 'Rue du moulin',
                        'adresse_facturation_numero_rue': '1',
                        'adresse_facturation_code_postal': '44000',
                        'adresse_facturation_ville': 'Nantes',
                        'adresse_facturation_pays': 'FR',
                        'adresse_facturation_destinataire': 'Jane Doe',
                        'adresse_facturation_boite_postale': 'PB1',
                        'copie_titre_sejour': [],
                        'documents_additionnels': [],
                    }
                )
            ),
            **self.default_kwargs,
        )

    def test_post_page_enrolment_as_professional_with_custom_belgian_billing_address(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'specific_questions-nom_siege_social': 'UCLouvain',
                'specific_questions-numero_unique_entreprise': '1234',
                'specific_questions-numero_tva_entreprise': '1234A',
                'specific_questions-adresse_mail_professionnelle': 'jane.doe@example.be',
                'specific_questions-type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                'specific_questions-adresse_facturation_destinataire': 'Jane Doe',
                'specific_questions-street': 'Rue du moulin',
                'specific_questions-street_number': '1',
                'specific_questions-be_postal_code': '1348',
                'specific_questions-be_city': 'Louvain-La-Neuve',
                'specific_questions-country': 'BE',
                'specific_questions-postal_box': 'PB1',
                'specific_questions-place': 'Avant',
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_continuing_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_continue_command=(
                ModifierQuestionsSpecifiquesFormationContinueCommand(
                    **{
                        'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                        'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                        'nom_siege_social': 'UCLouvain',
                        'numero_unique_entreprise': '1234',
                        'numero_tva_entreprise': '1234A',
                        'adresse_mail_professionnelle': 'jane.doe@example.be',
                        'type_adresse_facturation': ChoixTypeAdresseFacturation.AUTRE.name,
                        'adresse_facturation_rue': 'Rue du moulin',
                        'adresse_facturation_numero_rue': '1',
                        'adresse_facturation_code_postal': '1348',
                        'adresse_facturation_ville': 'Louvain-La-Neuve',
                        'adresse_facturation_pays': 'BE',
                        'adresse_facturation_destinataire': 'Jane Doe',
                        'adresse_facturation_boite_postale': 'PB1',
                        'copie_titre_sejour': [],
                        'documents_additionnels': [],
                    }
                )
            ),
            **self.default_kwargs,
        )
