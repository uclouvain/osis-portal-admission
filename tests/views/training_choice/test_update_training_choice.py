# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
from unittest.mock import mock_open

from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext as _
from osis_admission_sdk.model.informations_specifiques_formation_continue_dto import (
    InformationsSpecifiquesFormationContinueDTO,
)
from waffle.testutils import override_switch

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import AdmissionType, TypeFormationChoisissable, ChoixMoyensDecouverteFormation
from admission.contrib.enums.state_iufc import StateIUFC
from admission.contrib.forms import EMPTY_VALUE
from admission.tests.views.training_choice import AdmissionTrainingChoiceFormViewTestCase


class GeneralAdmissionUpdateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:general-education:update:training-choice', pk=cls.proposition_uuid)

    def test_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dependsOn.min.js", count=1)
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )

        # Initial values
        self.assertEqual(form.initial['double_degree_scholarship'], self.double_degree_scholarship.uuid)
        self.assertEqual(form.initial['international_scholarship'], self.international_scholarship.uuid)
        self.assertEqual(form.initial['erasmus_mundus_scholarship'], self.first_erasmus_mundus_scholarship.uuid)
        self.assertEqual(form.initial['general_education_training'], 'TR1-2020')
        self.assertEqual(form.fields['campus'].initial, EMPTY_VALUE)
        self.assertEqual(form.fields['training_type'].initial, TypeFormationChoisissable.MASTER.name)
        self.assertTrue(form.fields['has_erasmus_mundus_scholarship'].initial)
        self.assertTrue(form.fields['has_international_scholarship'].initial)
        self.assertTrue(form.fields['has_double_degree_scholarship'].initial)

        # Initial choices
        self.assertEqual(
            form.fields['campus'].choices,
            [
                (EMPTY_VALUE, _('All')),
                (self.louvain_campus_uuid, 'Louvain-La-Neuve'),
                (self.mons_campus_uuid, 'Mons'),
            ],
        )

        self.assertEqual(
            form.fields['general_education_training'].widget.choices,
            [
                ('TR1-2020', 'Formation 1 (Louvain-La-Neuve) <span class="training-acronym">TR1</span>'),
            ],
        )

    def test_form_submitting_missing_fields(self):
        response = self.client.post(self.url, data={'campus': EMPTY_VALUE})

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('training_type' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['training_type'])

    def test_form_submitting_missing_fields_with_master(self):
        response = self.client.post(
            self.url,
            data={
                'campus': EMPTY_VALUE,
                'training_type': TypeFormationChoisissable.MASTER.name,
            },
        )

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('general_education_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['general_education_training'])

        self.assertTrue('has_double_degree_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_double_degree_scholarship'])

        self.assertTrue('has_international_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_international_scholarship'])

        self.assertTrue('has_erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_erasmus_mundus_scholarship'])

    def test_form_submitting_missing_scholarship_fields_with_master(self):
        response = self.client.post(
            self.url,
            data={
                'campus': EMPTY_VALUE,
                'training_type': TypeFormationChoisissable.MASTER.name,
                'has_double_degree_scholarship': True,
                'has_international_scholarship': True,
                'has_erasmus_mundus_scholarship': True,
            },
        )

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('general_education_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['general_education_training'])

        self.assertTrue('double_degree_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['double_degree_scholarship'])

        self.assertTrue('international_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['international_scholarship'])

        self.assertTrue('erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['erasmus_mundus_scholarship'])

    def test_form_submitting_other_context(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
        }
        response = self.client.post(self.url, data=data)
        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertTrue('__all__' in form.errors)
        self.assertIn(
            _('To choose this course, you need to <a href="%(url)s">cancel</a> your application and create a new one.')
            % {'url': resolve_url(f'admission:general-education:cancel', pk=self.proposition_uuid)},
            form.errors['__all__'][0],
        )

    def test_form_submitting_valid_data(self):
        response = self.client.post(
            self.url,
            data={
                'campus': EMPTY_VALUE,
                'training_type': TypeFormationChoisissable.MASTER.name,
                'general_education_training': 'TR1-2020',
                'has_double_degree_scholarship': True,
                'has_international_scholarship': True,
                'has_erasmus_mundus_scholarship': True,
                'double_degree_scholarship': self.double_degree_scholarship.uuid,
                'international_scholarship': self.international_scholarship.uuid,
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
                'specific_question_answers_1': 'Answer',
            },
        )

        self.mock_proposition_api.return_value.update_general_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_generale_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR1',
                'annee_formation': 2020,
                'bourse_double_diplome': self.double_degree_scholarship.uuid,
                'bourse_internationale': self.international_scholarship.uuid,
                'bourse_erasmus_mundus': self.first_erasmus_mundus_scholarship.uuid,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)


class ContinuingAdmissionUpdateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:continuing-education:update:training-choice', pk=cls.proposition_uuid)

    def test_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )

        # Initial values
        self.assertEqual(form.initial['mixed_training'], 'TR2-2020')
        self.assertEqual(form.fields['campus'].initial, EMPTY_VALUE)
        self.assertEqual(form.fields['training_type'].initial, TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name)

        # Initial choices
        self.assertEqual(
            form.fields['campus'].choices,
            [
                (EMPTY_VALUE, _('All')),
                (self.louvain_campus_uuid, 'Louvain-La-Neuve'),
                (self.mons_campus_uuid, 'Mons'),
            ],
        )

        self.assertEqual(
            form.fields['mixed_training'].widget.choices,
            [
                ('TR2-2020', 'Formation 2 (Louvain-La-Neuve) <span class="training-acronym">TR2</span>'),
            ],
        )

        # A message is displayed for the HUE candidates
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        mock_proposition = self.mock_proposition_api.return_value.retrieve_continuing_education_proposition.return_value
        mock_proposition.pays_nationalite_ue_candidat = None

        response = self.client.get(self.url)
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        mock_proposition.pays_nationalite_ue_candidat = False
        response = self.client.get(self.url)
        self.assertIn('Les programmes certifiants et courts', response.rendered_content)

    def test_form_submitting_missing_fields_with_long_training(self):
        # The training is missing
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
        }
        response = self.client.post(self.url, data=data)
        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertTrue('mixed_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['mixed_training'])

        # The motivation and the ways of founding out about the training are missing
        response = self.client.post(self.url, data={'mixed_training': 'TR2-2020', **data})

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

    def test_form_submitting_missing_fields_with_short_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=False,
                etat=StateIUFC.OPEN.name,
            )
        )

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('motivations', form.errors)
        # For short courses, the ways of finding out about the course is not required
        self.assertNotIn('ways_to_find_out_about_the_course', form.errors)

    def test_form_submitting_other_context(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
            'motivations': 'Motivation',
            'ways_to_find_out_about_the_course': [ChoixMoyensDecouverteFormation.FACEBOOK.name],
        }
        response = self.client.post(self.url, data=data)
        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertTrue('__all__' in form.errors)
        self.assertIn(
            _('To choose this course, you need to <a href="%(url)s">cancel</a> your application and create a new one.')
            % {'url': resolve_url(f'admission:continuing-education:cancel', pk=self.proposition_uuid)},
            form.errors['__all__'][0],
        )

    def test_form_submitting_valid_data_with_long_training(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
            'specific_question_answers_1': 'Answer',
            'motivations': 'Motivation',
            'ways_to_find_out_about_the_course': [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
            ],
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'Motivation',
                'moyens_decouverte_formation': [
                    ChoixMoyensDecouverteFormation.FACEBOOK.name,
                    ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
                ],
                'autre_moyen_decouverte_formation': '',
                'marque_d_interet': None,
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)

    def test_form_submitting_valid_data_with_short_training(self):
        # For short courses, the ways of finding out about the course is not required
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=False,
                etat=StateIUFC.OPEN.name,
            )
        )

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
            'specific_question_answers_1': 'Answer',
            'motivations': 'Motivation',
            'ways_to_find_out_about_the_course': [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.COURRIER_PERSONNALISE.name,
            ],
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'Motivation',
                'moyens_decouverte_formation': [],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)

    def test_continuing_education_form_submitting_for_a_short_opened_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=False,
                etat=StateIUFC.OPEN.name,
            )
        )

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'mixed_training': 'TR2-2020',
            'specific_question_answers_1': 'Answer',
        }

        # With missing data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

        data['motivations'] = 'My motivation'

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        # With extra data
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name]
        data['interested_mark'] = True

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

    def test_continuing_education_form_submitting_for_a_short_closed_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=False,
                etat=StateIUFC.CLOSED.name,
            )
        )

        data = {
            'specific_question_answers_1': 'Answer',
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'mixed_training': 'TR2-2020',
        }

        # With missing data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertNotIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

        data['motivations'] = 'My motivation'
        data['interested_mark'] = True

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [],
                'marque_d_interet': True,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        # With extra data
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name]

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [],
                'marque_d_interet': True,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

    def test_continuing_education_form_submitting_for_a_long_opened_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=True,
                etat=StateIUFC.OPEN.name,
            )
        )

        data = {
            'specific_question_answers_1': 'Answer',
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'mixed_training': 'TR2-2020',
        }

        # With missing data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

        data['motivations'] = 'My motivation'
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name]

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        # With extra data
        data['interested_mark'] = True

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

    def test_continuing_education_form_submitting_for_a_long_closed_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO._from_openapi_data(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=True,
                etat=StateIUFC.CLOSED.name,
            )
        )

        data = {
            'specific_question_answers_1': 'Answer',
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'mixed_training': 'TR2-2020',
        }

        # With missing data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

        data['motivations'] = 'My motivation'
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name]
        data['other_way_to_find_out_about_the_course'] = 'Other way'
        data['interested_mark'] = True

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name],
                'marque_d_interet': True,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        # With another way
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.AUTRE.name]
        data['other_way_to_find_out_about_the_course'] = ''

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_way_to_find_out_about_the_course', []))

        # With complete data
        data['other_way_to_find_out_about_the_course'] = 'Other way'

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.update_continuing_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_choix_formation_continue_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.AUTRE.name],
                'marque_d_interet': True,
                'autre_moyen_decouverte_formation': 'Other way',
            },
            **self.default_kwargs,
        )


@override_switch('admission-doctorat', active=True)
class DoctorateAdmissionUpdateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:doctorate:update:training-choice', pk=cls.proposition_uuid)

    def test_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, 200)
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )

        # Initial values
        self.assertEqual(form.initial['doctorate_training'], 'TR3-2020')
        self.assertEqual(form.fields['campus'].initial, EMPTY_VALUE)
        self.assertEqual(form.fields['training_type'].initial, TypeFormationChoisissable.DOCTORAT.name)
        self.assertEqual(form.initial['proximity_commission'], 'MANAGEMENT')
        self.assertEqual(form.fields['proximity_commission_cde'].initial, 'MANAGEMENT')

        # Initial choices
        self.assertEqual(
            form.fields['campus'].choices,
            [
                (EMPTY_VALUE, _('All')),
                (self.louvain_campus_uuid, 'Louvain-La-Neuve'),
                (self.mons_campus_uuid, 'Mons'),
            ],
        )

        expected = [
            {
                'id': 'TR3-2020',
                'sigle': 'TR3',
                'sigle_entite_gestion': 'CDE',
                'text': 'Formation 3 (Louvain-La-Neuve) <span class="training-acronym">TR3</span>',
            }
        ]
        self.assertEqual(form.fields['doctorate_training'].widget.attrs['data-data'], json.dumps(expected))

    def test_redirection_if_the_related_action_is_forbidden(self):
        with mock.patch.object(self.doctorate_proposition, 'links', {}):
            self.mock_proposition_api.return_value.retrieve_doctorate_proposition.side_effect = None
            self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value = (
                self.doctorate_proposition
            )
            response = self.client.get(self.url)

            self.assertRedirects(
                response=response,
                expected_url=reverse('admission:doctorate:training-choice', args=[self.doctorate_proposition.uuid]),
            )

    def test_form_submitting_missing_training_type_field(self):
        response = self.client.post(self.url)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue('training_type' in form.errors)

    def test_form_submitting_missing_fields(self):
        response = self.client.post(self.url, {'training_type': TypeFormationChoisissable.DOCTORAT.name})
        form = response.context['form']
        self.assertFalse(form.is_valid())

        self.assertTrue('admission_type' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['admission_type'])

    def test_form_submitting_missing_pre_admission_comment_field(self):
        data = {
            'training_type': TypeFormationChoisissable.DOCTORAT.name,
            'admission_type': AdmissionType.PRE_ADMISSION.name,
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('justification' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['justification'])

    def test_form_submitting_valid_data(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormationChoisissable.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'sector': 'SSH',
                'doctorate_training': 'TR3-2020',
                'proximity_commission_cde': 'ECONOMY',
                'admission_type': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'specific_question_answers_1': 'Answer',
            },
        )

        self.mock_proposition_api.return_value.update_doctorate_training_choice.assert_called_with(
            uuid=self.proposition_uuid,
            modifier_type_admission_doctorale_command={
                'uuid_proposition': self.proposition_uuid,
                'sigle_formation': 'TR3',
                'annee_formation': 2020,
                'commission_proximite': 'ECONOMY',
                'type_admission': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)
