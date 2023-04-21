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

from django.shortcuts import resolve_url
from django.utils.translation import gettext as _
from rest_framework import status

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import AdmissionType, TypeFormationChoisissable
from admission.contrib.enums.training_choice import TypeFormation
from admission.contrib.forms import EMPTY_VALUE
from admission.tests.views.training_choice import AdmissionTrainingChoiceFormViewTestCase


class AdmissionCreateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:create:training-choice')

    def test_empty_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "dependsOn.min.js", count=1)

        self.assertEqual(
            form.fields['campus'].choices,
            [
                (EMPTY_VALUE, _('All')),
                (self.louvain_campus_uuid, 'Louvain-La-Neuve'),
                (self.mons_campus_uuid, 'Mons'),
            ],
        )

        self.assertEqual(
            form.fields['sector'].widget.choices,
            (
                ('', ' - '),
                ('SSH', 'SSH - Foobar'),
                ('SST', 'SST - Barbaz'),
                ('SSS', 'SSS - Foobarbaz'),
            ),
        )

        self.assertFalse(form.fields['has_erasmus_mundus_scholarship'].initial)
        self.assertFalse(form.fields['has_international_scholarship'].initial)
        self.assertFalse(form.fields['has_double_degree_scholarship'].initial)

    def test_empty_form_submitting(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': '',
                'campus': EMPTY_VALUE,
            },
        )

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('training_type' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['training_type'])

    def test_continuing_education_form_submitting_without_training(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('mixed_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['mixed_training'])

    def test_continuing_education_form_submitting(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:continuing-education:update:training-choice', pk=self.proposition_uuid),
        )

    def test_general_education_form_submitting_without_required_fields(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.MASTER.name,
                'campus': EMPTY_VALUE,
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

    def test_general_education_form_submitting_without_required_scholarship_fields(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.MASTER.name,
                'campus': EMPTY_VALUE,
                'has_double_degree_scholarship': True,
                'has_international_scholarship': True,
                'has_erasmus_mundus_scholarship': True,
            },
        )

        form = response.context['form']
        self.assertFalse(form.is_valid())

        self.assertTrue('double_degree_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['double_degree_scholarship'])

        self.assertTrue('international_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['international_scholarship'])

        self.assertTrue('erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['erasmus_mundus_scholarship'])

    def test_general_education_form_submitting(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.MASTER.name,
                'campus': EMPTY_VALUE,
                'general_education_training': 'TR1-2020',
                'has_double_degree_scholarship': True,
                'has_international_scholarship': True,
                'has_erasmus_mundus_scholarship': True,
                'double_degree_scholarship': self.double_degree_scholarship.uuid,
                'international_scholarship': self.international_scholarship.uuid,
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
            },
        )

        self.mock_proposition_api.return_value.create_general_training_choice.assert_called_with(
            initier_proposition_generale_command={
                'sigle_formation': 'TR1',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'bourse_double_diplome': self.double_degree_scholarship.uuid,
                'bourse_internationale': self.international_scholarship.uuid,
                'bourse_erasmus_mundus': self.first_erasmus_mundus_scholarship.uuid,
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:general-education:update:training-choice', pk=self.proposition_uuid),
        )

    def test_general_education_form_submitting_mixed_training(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.create_general_training_choice.assert_called_with(
            initier_proposition_generale_command={
                'sigle_formation': 'TR5',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'bourse_erasmus_mundus': '',
                'bourse_double_diplome': '',
                'bourse_internationale': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:general-education:update:training-choice', pk=self.proposition_uuid),
        )

    def test_doctorate_education_form_submitting_without_required_fields(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
            },
        )

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('doctorate_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['doctorate_training'])

        self.assertTrue('admission_type' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['admission_type'])

        self.assertTrue('sector' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['sector'])

        self.assertTrue('has_erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_erasmus_mundus_scholarship'])

    def test_doctorate_education_form_submitting_without_required_pre_admission_fields(self):
        data = {
            'training_type': TypeFormation.DOCTORAT.name,
            'campus': EMPTY_VALUE,
            'admission_type': AdmissionType.PRE_ADMISSION.name,
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertTrue('justification' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['justification'])

    def test_doctorate_education_form_submitting_without_required_fields_cde(self):
        # Some doctorates require a CDE proximity commission
        data = {
            'training_type': TypeFormation.DOCTORAT.name,
            'campus': EMPTY_VALUE,
            'doctorate_training': 'TR3-2020',
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertTrue('proximity_commission_cde' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['proximity_commission_cde'])

    def test_doctorate_education_form_submitting_without_required_fields_cdss(self):
        data = {
            'training_type': TypeFormation.DOCTORAT.name,
            'campus': EMPTY_VALUE,
            'doctorate_training': 'TR4-2020',
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertTrue('proximity_commission_cdss' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['proximity_commission_cdss'])

    def test_doctorate_education_form_submitting_without_required_fields_science_sub_domain(self):
        # Some doctorates require a science sub domain
        data = {
            'training_type': TypeFormation.DOCTORAT.name,
            'campus': EMPTY_VALUE,
            'doctorate_training': 'SC3DP-2020',
        }
        response = self.client.post(self.url, data=data)

        form = response.context['form']

        self.assertTrue('science_sub_domain' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['science_sub_domain'])

    def test_doctorate_education_form_submitting_sc3dp(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'doctorate_training': 'SC3DP-2020',
                'sector': 'SSH',
                'has_erasmus_mundus_scholarship': True,
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
                'admission_type': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'type_admission': AdmissionType.PRE_ADMISSION.name,
                'sigle_formation': 'SC3DP',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': 'Justification',
                'commission_proximite': 'MATHEMATICS',
                'bourse_erasmus_mundus': self.first_erasmus_mundus_scholarship.uuid,
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:doctorate:update:training-choice', pk=self.proposition_uuid),
        )

    def test_doctorate_education_form_submitting_cde(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'doctorate_training': 'TR3-2020',
                'sector': 'SSH',
                'has_erasmus_mundus_scholarship': False,
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
                'admission_type': AdmissionType.ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'type_admission': AdmissionType.ADMISSION.name,
                'sigle_formation': 'TR3',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': '',
                'commission_proximite': 'ECONOMY',
                'bourse_erasmus_mundus': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:doctorate:update:training-choice', pk=self.proposition_uuid),
        )

    def test_doctorate_education_form_submitting_cdss(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'doctorate_training': 'TR4-2020',
                'sector': 'SSH',
                'has_erasmus_mundus_scholarship': False,
                'erasmus_mundus_scholarship': self.first_erasmus_mundus_scholarship.uuid,
                'admission_type': AdmissionType.ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'type_admission': AdmissionType.ADMISSION.name,
                'sigle_formation': 'TR4',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': '',
                'commission_proximite': 'ECLI',
                'bourse_erasmus_mundus': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:doctorate:update:training-choice', pk=self.proposition_uuid),
        )
