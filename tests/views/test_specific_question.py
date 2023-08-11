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
from datetime import datetime
from unittest.mock import patch, ANY

from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.status import HTTP_200_OK

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.additional_information import ChoixInscriptionATitre, ChoixTypeAdresseFacturation
from admission.contrib.enums.specific_question import Onglets
from admission.contrib.forms import PDF_MIME_TYPE
from admission.tests.views.training_choice import AdmissionTrainingChoiceFormViewTestCase


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
        self.assertContains(response, _("Course change"))

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
        self.assertContains(response, _("Enrolment in limited enrolment bachelor's course"))


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
        self.assertEqual(response.context['admission'].uuid, self.bachelor_proposition.uuid)
        self.assertEqual(response.context['specific_questions'], self.specific_questions)
        self.assertEqual(
            response.context['forms'][0].initial,
            {
                'reponses_questions_specifiques': self.bachelor_proposition.reponses_questions_specifiques,
                'documents_additionnels': self.bachelor_proposition.documents_additionnels,
            },
        )

    def test_post_page(self):
        response = self.client.post(
            self.url,
            data={
                'specific_questions-reponses_questions_specifiques_1': 'My updated answer',
                'specific_questions-documents_additionnels_0': 'uuid-doc',
            },
        )

        self.assertRedirects(response, self.url)
        self.mock_proposition_api.return_value.update_general_specific_question.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_questions_specifiques_formation_generale_command={
                'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                'documents_additionnels': ['uuid-doc'],
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
            'specific_questions-reponses_questions_specifiques_1': 'Answer',
        }
        response = self.client.post(self.url, data=data)
        self.assertRedirects(response, self.url)

        self.mock_proposition_api.return_value.update_pool_questions.assert_called_with(
            uuid=self.proposition_uuid,
            pool_questions={
                'is_belgian_bachelor': True,
                'is_external_reorientation': True,
                'regular_registration_proof': [],
            },
            **self.default_kwargs,
        )
        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
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
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_reorientation': True,
            'pool_questions-regular_registration_proof_0': 'uuid',
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
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_reorientation': False,
            'pool_questions-regular_registration_proof_0': 'uuid',
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
        self.assertContains(response, _("Change of enrolment"))
        self.assertContains(response, '30/03/2023 23:59')

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': 'Foo'})
        self.assertIn('is_belgian_bachelor', response.context['forms'][1].errors)

        response = self.client.post(self.url, data={'pool_questions-is_belgian_bachelor': True})
        self.assertIn('is_external_modification', response.context['forms'][1].errors)

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form': [],
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
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
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
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': False,
            'pool_questions-is_external_modification': True,
            'pool_questions-registration_change_form_0': 'uuid',
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
            },
            **self.default_kwargs,
        )

        data = {
            'pool_questions-is_belgian_bachelor': True,
            'pool_questions-is_external_modification': False,
            'pool_questions-registration_change_form_0': 'uuid',
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
            },
            **self.default_kwargs,
        )


class ContinuingEducationSpecificQuestionFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:update:specific-questions', pk=cls.proposition_uuid)

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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
        mock_retrieve_proposition = self.mock_proposition_api.return_value.retrieve_continuing_education_proposition
        mock_retrieve_proposition.return_value.pays_nationalite_ue_candidat = True
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
            modifier_questions_specifiques_formation_continue_command={
                'reponses_questions_specifiques': ANY,
                'inscription_a_titre': ANY,
                'copie_titre_sejour': [],
                'documents_additionnels': ['file-token1'],
            },
            **self.default_kwargs,
        )

        mock_retrieve_proposition.return_value.pays_nationalite_ue_candidat = False
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
            modifier_questions_specifiques_formation_continue_command={
                'reponses_questions_specifiques': ANY,
                'inscription_a_titre': ANY,
                'copie_titre_sejour': ['file-token'],
                'documents_additionnels': [],
            },
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
            modifier_questions_specifiques_formation_continue_command={
                'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                'inscription_a_titre': ChoixInscriptionATitre.PRIVE.name,
                'copie_titre_sejour': [],
                'documents_additionnels': [],
            },
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
            modifier_questions_specifiques_formation_continue_command={
                'reponses_questions_specifiques': {self.first_question_uuid: 'My updated answer'},
                'inscription_a_titre': ChoixInscriptionATitre.PROFESSIONNEL.name,
                'nom_siege_social': 'UCLouvain',
                'numero_unique_entreprise': '1234',
                'numero_tva_entreprise': '1234A',
                'adresse_mail_professionnelle': 'jane.doe@example.be',
                'type_adresse_facturation': ChoixTypeAdresseFacturation.RESIDENTIEL.name,
                'copie_titre_sejour': [],
                'documents_additionnels': [],
            },
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

        self.assertEqual(response.status_code, HTTP_200_OK)
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
            modifier_questions_specifiques_formation_continue_command={
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
            },
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
            modifier_questions_specifiques_formation_continue_command={
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
            },
            **self.default_kwargs,
        )
