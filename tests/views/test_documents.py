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
import datetime
import uuid
from unittest.mock import ANY, MagicMock, patch

from django.core.exceptions import ValidationError
from django.shortcuts import resolve_url
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy
from osis_admission_sdk.model.document_specific_question import DocumentSpecificQuestion
from osis_admission_sdk.model.document_specific_questions_list import (
    DocumentSpecificQuestionsList,
)

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    ChoixStatutPropositionContinue,
    ChoixStatutPropositionDoctorale,
    CleConfigurationItemFormulaire,
    TrainingType,
    TypeItemFormulaire,
)
from admission.contrib.enums.projet import ChoixStatutPropositionGenerale
from admission.contrib.forms import JPEG_MIME_TYPE, PDF_MIME_TYPE
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


class BaseDocumentsFormViewTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.documents_to_complete_immediately_configurations = [
            DocumentSpecificQuestion(
                uuid='CURRICULUM.MON_DOCUMENT_1',
                type=TypeItemFormulaire.DOCUMENT.name,
                title={
                    'fr-be': 'Premier document',
                    'en': 'First document',
                },
                text={
                    'fr-be': 'La première raison',
                    'en': 'The first reason',
                },
                help_text={},
                configuration={
                    CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: [PDF_MIME_TYPE],
                },
                values=[],
                tab='CURRICULUM',
                tab_name='Curriculum',
                required=True,
            ),
            DocumentSpecificQuestion(
                uuid='CHOIX_FORMATION.MON_DOCUMENT_2',
                type=TypeItemFormulaire.DOCUMENT.name,
                title={
                    'fr-be': 'Deuxième document',
                    'en': 'Second document',
                },
                text={
                    'fr-be': 'La deuxième raison',
                    'en': 'The second reason',
                },
                help_text={},
                configuration={
                    CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: [JPEG_MIME_TYPE],
                },
                values=[],
                tab='CHOIX_FORMATION',
                tab_name='Course choice',
                required=True,
            ),
        ]
        cls.documents_to_complete_later_configurations = [
            DocumentSpecificQuestion(
                uuid='CURRICULUM.MON_DOCUMENT_3',
                type=TypeItemFormulaire.DOCUMENT.name,
                title={
                    'fr-be': 'Troisième document',
                    'en': 'Third document',
                },
                text={
                    'fr-be': 'La troisième raison',
                    'en': 'The third reason',
                },
                help_text={},
                configuration={
                    CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name: [PDF_MIME_TYPE],
                },
                values=[],
                tab='CURRICULUM',
                tab_name='Curriculum',
                required=False,
            ),
        ]

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        # Mock osis document api
        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            side_effect=lambda token: {
                "name": "myfile",
                'size': 1,
                'mimetype': {
                    'pdf_file': PDF_MIME_TYPE,
                    'jpeg_file': JPEG_MIME_TYPE,
                    'facultative_pdf_file': PDF_MIME_TYPE,
                }[token],
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.client.force_login(self.person.user)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class GeneralDocumentsFormViewTestCase(BaseDocumentsFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links={'update_documents': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={},
        )

        cls.url = resolve_url('admission:general-education:update:documents', pk=cls.proposition.uuid)
        cls.confirm_url = resolve_url('admission:general-education:update:confirm-documents', pk=cls.proposition.uuid)

    def setUp(self):
        super().setUp()

        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.list_general_documents.return_value = DocumentSpecificQuestionsList(
            immediate_requested_documents=self.documents_to_complete_immediately_configurations,
            later_requested_documents=self.documents_to_complete_later_configurations,
            deadline=datetime.date(2023, 1, 1),
        )

        self.addCleanup(propositions_api_patcher.stop)

    def test_redirect_to_admission_list_if_no_permission(self):
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value.links = {}

        response = self.client.get(self.url)

        self.assertRedirects(
            response=response,
            expected_url=reverse('admission:list'),
            fetch_redirect_response=False,
        )

    def test_display_document_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_general_documents.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        form = response.context['form']
        mandatory_fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertEqual(len(mandatory_fields), 2)

        self.assertEqual(mandatory_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(mandatory_fields[0].required, True)

        self.assertEqual(mandatory_fields[1].mimetypes, [JPEG_MIME_TYPE])
        self.assertEqual(mandatory_fields[1].required, True)

        facultative_fields = form.fields['reponses_documents_a_completer__1'].fields
        self.assertEqual(len(facultative_fields), 1)

        self.assertEqual(facultative_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(facultative_fields[0].required, False)

    def test_submit_document_form(self):
        # Submit an invalid form
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertFalse(form.is_valid())
        self.assertTrue('reponses_documents_a_completer__0' in form.errors)
        self.assertIn(ValidationError(FIELD_REQUIRED_MESSAGE), getattr(fields[1], 'errors', []))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, gettext_lazy('Required documents are missing.'))

        # Submit a valid form with only mandatory fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_general_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': [],
                },
            },
            **self.default_kwargs,
        )

        # Submit a valid form with mandatory and facultative fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
                'reponses_documents_a_completer__1_0_0': ['facultative_pdf_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_general_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': ['facultative_pdf_file'],
                },
            },
            **self.default_kwargs,
        )

    def test_confirm_document_page(self):
        # Only access to the confirmation page through the document form page
        response = self.client.get(self.confirm_url)
        self.assertEqual(response.status_code, 403)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ContinuingDocumentsFormViewTestCase(BaseDocumentsFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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
            statut=ChoixStatutPropositionContinue.EN_BROUILLON.name,
            links={'update_documents': {'url': 'ok'}},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={},
        )

        cls.url = resolve_url('admission:continuing-education:update:documents', pk=cls.proposition.uuid)
        cls.confirm_url = resolve_url(
            'admission:continuing-education:update:confirm-documents',
            pk=cls.proposition.uuid,
        )

    def setUp(self):
        super().setUp()

        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.list_continuing_documents.return_value = DocumentSpecificQuestionsList(
            immediate_requested_documents=self.documents_to_complete_immediately_configurations,
            later_requested_documents=self.documents_to_complete_later_configurations,
            deadline=datetime.date(2023, 1, 1),
        )

        self.addCleanup(propositions_api_patcher.stop)

    def test_display_document_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_continuing_documents.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        form = response.context['form']
        mandatory_fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertEqual(len(mandatory_fields), 2)

        self.assertEqual(mandatory_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(mandatory_fields[0].required, True)

        self.assertEqual(mandatory_fields[1].mimetypes, [JPEG_MIME_TYPE])
        self.assertEqual(mandatory_fields[1].required, True)

        facultative_fields = form.fields['reponses_documents_a_completer__1'].fields
        self.assertEqual(len(facultative_fields), 1)

        self.assertEqual(facultative_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(facultative_fields[0].required, False)

    def test_submit_document_form(self):
        # Submit an invalid form
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertFalse(form.is_valid())
        self.assertTrue('reponses_documents_a_completer__0' in form.errors)
        self.assertIn(ValidationError(FIELD_REQUIRED_MESSAGE), getattr(fields[1], 'errors', []))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, gettext_lazy('Required documents are missing.'))

        # Submit a valid form with only mandatory fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_continuing_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': [],
                },
            },
            **self.default_kwargs,
        )

        # Submit a valid form with mandatory and facultative fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
                'reponses_documents_a_completer__1_0_0': ['facultative_pdf_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_continuing_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': ['facultative_pdf_file'],
                },
            },
            **self.default_kwargs,
        )

    def test_confirm_document_page(self):
        # Only access to the confirmation page through the document form page
        response = self.client.get(self.confirm_url)
        self.assertEqual(response.status_code, 403)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class DoctorateDocumentsFormViewTestCase(BaseDocumentsFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.proposition = MagicMock(
            uuid=str(uuid.uuid4()),
            doctorat=MagicMock(
                annee=2020,
                intitule='Formation',
                campus='Mons',
                sigle='TR1',
                type=TrainingType.MASTER_M1.name,
            ),
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            links={'update_documents': {'url': 'ok'}},
            erreurs={},
            reponses_questions_specifiques={},
        )

        cls.url = resolve_url('admission:doctorate:update:documents', pk=cls.proposition.uuid)
        cls.confirm_url = resolve_url('admission:doctorate:update:confirm-documents', pk=cls.proposition.uuid)

    def setUp(self):
        super().setUp()

        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()

        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value = self.proposition
        self.mock_proposition_api.return_value.list_doctorate_documents.return_value = DocumentSpecificQuestionsList(
            immediate_requested_documents=self.documents_to_complete_immediately_configurations,
            later_requested_documents=self.documents_to_complete_later_configurations,
            deadline=datetime.date(2023, 1, 1),
        )

        self.addCleanup(propositions_api_patcher.stop)

    def test_display_document_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        # Check api calls
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        self.mock_proposition_api.return_value.list_doctorate_documents.assert_called_with(
            uuid=self.proposition.uuid,
            **self.default_kwargs,
        )

        form = response.context['form']
        mandatory_fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertEqual(len(mandatory_fields), 2)

        self.assertEqual(mandatory_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(mandatory_fields[0].required, True)

        self.assertEqual(mandatory_fields[1].mimetypes, [JPEG_MIME_TYPE])
        self.assertEqual(mandatory_fields[1].required, True)

        facultative_fields = form.fields['reponses_documents_a_completer__1'].fields
        self.assertEqual(len(facultative_fields), 1)

        self.assertEqual(facultative_fields[0].mimetypes, [PDF_MIME_TYPE])
        self.assertEqual(facultative_fields[0].required, False)

    def test_submit_document_form(self):
        # Submit an invalid form
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        fields = form.fields['reponses_documents_a_completer__0'].fields
        self.assertFalse(form.is_valid())
        self.assertTrue('reponses_documents_a_completer__0' in form.errors)
        self.assertIn(ValidationError(FIELD_REQUIRED_MESSAGE), getattr(fields[1], 'errors', []))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message, gettext_lazy('Required documents are missing.'))

        # Submit a valid form with only mandatory fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_doctorate_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': [],
                },
            },
            **self.default_kwargs,
        )

        # Submit a valid form with mandatory and facultative fields
        response = self.client.post(
            self.url,
            data={
                'reponses_documents_a_completer__0_0_0': ['pdf_file'],
                'reponses_documents_a_completer__0_1_0': ['jpeg_file'],
                'reponses_documents_a_completer__1_0_0': ['facultative_pdf_file'],
            },
        )

        self.assertRedirects(response, self.confirm_url)

        # Check API calls
        self.mock_proposition_api.return_value.create_doctorate_documents.assert_called_with(
            uuid=self.proposition.uuid,
            completer_emplacements_documents_par_candidat_command={
                'reponses_documents_a_completer': {
                    'CURRICULUM.MON_DOCUMENT_1': ['pdf_file'],
                    'CHOIX_FORMATION.MON_DOCUMENT_2': ['jpeg_file'],
                    'CURRICULUM.MON_DOCUMENT_3': ['facultative_pdf_file'],
                },
            },
            **self.default_kwargs,
        )

    def test_confirm_document_page(self):
        # Only access to the confirmation page through the document form page
        response = self.client.get(self.confirm_url)
        self.assertEqual(response.status_code, 403)
