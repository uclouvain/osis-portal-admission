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

import json

from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from rest_framework import status

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import AdmissionType, TypeFormationChoisissable
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
                ('TR1-2020', 'Formation 1 (Louvain-La-Neuve) - TR1'),
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

    def test_form_submitting_missing_scholarshipfields_with_master(self):
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
            _(
                'To choose this training, you need to <a href="%(url)s">cancel</a> '
                'the current application and create a new one.'
            )
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

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
                ('TR2-2020', 'Formation 2 (Louvain-La-Neuve) - TR2'),
            ],
        )

    def test_form_submitting_missing_fields(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
        }
        response = self.client.post(self.url, data=data)
        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertTrue('mixed_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['mixed_training'])

    def test_form_submitting_other_context(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
        }
        response = self.client.post(self.url, data=data)
        form = response.context['form']

        self.assertFalse(form.is_valid())
        self.assertTrue('__all__' in form.errors)
        self.assertIn(
            _(
                'To choose this training, you need to <a href="%(url)s">cancel</a> '
                'the current application and create a new one.'
            )
            % {'url': resolve_url(f'admission:continuing-education:cancel', pk=self.proposition_uuid)},
            form.errors['__all__'][0],
        )

    def test_form_submitting_valid_data(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
            'specific_question_answers_1': 'Answer',
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
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)


class DoctorateAdmissionUpdateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:doctorate:update:training-choice', pk=cls.proposition_uuid)

    def test_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called_with(
            uuid=self.proposition_uuid,
            **self.default_kwargs,
        )

        # Initial values
        self.assertEqual(form.initial['erasmus_mundus_scholarship'], self.first_erasmus_mundus_scholarship.uuid)
        self.assertEqual(form.initial['doctorate_training'], 'TR3-2020')
        self.assertEqual(form.fields['campus'].initial, EMPTY_VALUE)
        self.assertEqual(form.fields['training_type'].initial, TypeFormationChoisissable.DOCTORAT.name)
        self.assertTrue(form.fields['has_erasmus_mundus_scholarship'].initial)
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
                'text': 'Formation 3 (Louvain-La-Neuve) - TR3',
            }
        ]
        self.assertEqual(form.fields['doctorate_training'].widget.attrs['data-data'], json.dumps(expected))

    def test_form_submitting_missing_training_type_field(self):
        response = self.client.post(self.url)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue('training_type' in form.errors)

    def test_form_submitting_missing_fields(self):
        response = self.client.post(self.url, {'training_type': TypeFormationChoisissable.DOCTORAT.name})
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue('has_erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_erasmus_mundus_scholarship'])

        self.assertTrue('admission_type' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['admission_type'])

    def test_form_submitting_missing_scholarship_fields(self):
        data = {
            'training_type': TypeFormationChoisissable.DOCTORAT.name,
            'has_erasmus_mundus_scholarship': True,
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['erasmus_mundus_scholarship'])

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
                'has_erasmus_mundus_scholarship': True,
                'admission_type': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
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
                'bourse_erasmus_mundus': self.first_erasmus_mundus_scholarship.uuid,
                'type_admission': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'reponses_questions_specifiques': {
                    self.first_question_uuid: 'Answer',
                },
            },
            **self.default_kwargs,
        )

        self.assertRedirects(response, self.url)
