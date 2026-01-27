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
from unittest.mock import MagicMock

import freezegun
from django.shortcuts import resolve_url
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from osis_admission_sdk.models.informations_specifiques_formation_continue_dto import (
    InformationsSpecifiquesFormationContinueDTO,
)
from waffle.testutils import override_switch

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import (
    AdmissionType,
    ChoixMoyensDecouverteFormation,
    TypeFormationChoisissable,
)
from admission.contrib.enums.state_iufc import StateIUFC
from admission.contrib.enums.training_choice import TypeFormation
from admission.contrib.forms import EMPTY_VALUE
from admission.tests.views.training_choice import (
    AdmissionTrainingChoiceFormViewTestCase,
)


@override_switch('admission-doctorat', active=True)
class AdmissionCreateTrainingChoiceFormViewTestCase(AdmissionTrainingChoiceFormViewTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = resolve_url('admission:create:training-choice')

    def test_empty_form_initialization(self):
        response = self.client.get(self.url)
        form = response.context['form']

        self.assertEqual(response.status_code, 200)
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
            [
                ('', ' - '),
                ('SSH', 'SSH - Foobar'),
                ('SST', 'SST - Barbaz'),
                ('SSS', 'SSS - Foobarbaz'),
            ],
        )

        self.assertFalse(form.fields['has_erasmus_mundus_scholarship'].initial)
        self.assertFalse(form.fields['has_international_scholarship'].initial)
        self.assertFalse(form.fields['has_double_degree_scholarship'].initial)

        # A message is displayed for the HUE candidates for a continuing education training
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        self.mock_person_api.return_value.retrieve_identification_dto.return_value = MagicMock(
            pays_nationalite_europeen=True,
        )
        response = self.client.get(self.url)
        self.assertNotIn('Les programmes certifiants et courts', response.rendered_content)

        self.mock_person_api.return_value.retrieve_identification_dto.return_value = MagicMock(
            pays_nationalite_europeen=False,
        )
        response = self.client.get(self.url)
        self.assertIn('Les programmes certifiants et courts', response.rendered_content)

        # A message is displayed if period dates are not respected
        medicine_start_date = date_format(
            datetime.date.fromisoformat(self.specific_periods.medicine_dentistry_bachelor['date_debut']),
            'j F Y',
        )

        for date in ['2021-09-14', '2022-02-16']:
            with freezegun.freeze_time(date):
                response = self.client.get(self.url)

                self.assertEqual(response.status_code, 200)

                period_messages = response.context.get('not_in_specific_enrolment_periods_messages')
                self.assertIsNotNone(period_messages)
                self.assertEqual(
                    period_messages.get('medicine_dentistry_bachelor'),
                    "Dans l’attente de la publication des résultats du concours d’entrée en "
                    "médecine et dentisterie, votre demande ne pourra être soumise qu'à partir "
                    "du {medicine_start_date}.".format(medicine_start_date=medicine_start_date),
                )

        for date in ['2021-09-15', '2022-02-15']:
            with freezegun.freeze_time(date):
                response = self.client.get(self.url)

                self.assertEqual(response.status_code, 200)

                period_messages = response.context.get('not_in_specific_enrolment_periods_messages')
                self.assertIsNotNone(period_messages)
                self.assertIsNone(period_messages.get('medicine_dentistry_bachelor'))

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

    def test_continuing_education_form_submitting_without_motivation_and_way_of_founding_the_training(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('motivations', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('ways_to_find_out_about_the_course', []))

    def test_continuing_education_form_submitting(self):
        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR2-2020',
            'motivations': 'My motivation',
            'ways_to_find_out_about_the_course': [
                ChoixMoyensDecouverteFormation.FACEBOOK.name,
                ChoixMoyensDecouverteFormation.LINKEDIN.name,
                ChoixMoyensDecouverteFormation.AUTRE.name,
            ],
            'other_way_to_find_out_about_the_course': 'Other way',
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [
                    ChoixMoyensDecouverteFormation.FACEBOOK.name,
                    ChoixMoyensDecouverteFormation.LINKEDIN.name,
                    ChoixMoyensDecouverteFormation.AUTRE.name,
                ],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': 'Other way',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:continuing-education:update:training-choice', pk=self.proposition_uuid),
        )

    def test_continuing_education_form_submitting_for_a_short_opened_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO(
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

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
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
        data['autre_moyen_decouverte_formation'] = 'My other way'

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
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
            InformationsSpecifiquesFormationContinueDTO(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=False,
                etat=StateIUFC.CLOSED.name,
            )
        )

        data = {
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

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
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

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
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
            InformationsSpecifiquesFormationContinueDTO(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=True,
                etat=StateIUFC.OPEN.name,
            )
        )

        data = {
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

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
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

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

        # With another way to find out about the course
        data['ways_to_find_out_about_the_course'] = [ChoixMoyensDecouverteFormation.AUTRE.name]
        data['other_way_to_find_out_about_the_course'] = ''

        # With missing data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('other_way_to_find_out_about_the_course', []))

        data['other_way_to_find_out_about_the_course'] = 'My other way'

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.AUTRE.name],
                'marque_d_interet': None,
                'autre_moyen_decouverte_formation': 'My other way',
            },
            **self.default_kwargs,
        )

    def test_continuing_education_form_submitting_for_a_long_closed_training(self):
        mock_continuing_api = self.mock_continuing_education_api.return_value
        mock_continuing_api.retrieve_informations_specifiques_formation_continue_dto.side_effect = lambda **kwargs: (
            InformationsSpecifiquesFormationContinueDTO(
                sigle_formation='TR2',
                annee=2020,
                aide_a_la_formation=True,
                inscription_au_role_obligatoire=True,
                etat=StateIUFC.CLOSED.name,
            )
        )

        data = {
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
        data['interested_mark'] = True

        # With complete data
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.create_continuing_training_choice.assert_called_with(
            initier_proposition_continue_command={
                'sigle_formation': 'TR2',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'motivations': 'My motivation',
                'moyens_decouverte_formation': [ChoixMoyensDecouverteFormation.BOUCHE_A_OREILLE.name],
                'marque_d_interet': True,
                'autre_moyen_decouverte_formation': '',
            },
            **self.default_kwargs,
        )

    def test_general_education_form_submitting_without_required_fields_for_a_master(self):
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

    def test_general_education_form_submitting_without_required_scholarship_fields_for_a_master(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.MASTER.name,
                'campus': EMPTY_VALUE,
                'general_education_training': 'TR1-2020',
            },
        )

        form = response.context['form']
        self.assertFalse(form.is_valid())

        self.assertTrue('has_double_degree_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_double_degree_scholarship'])

        self.assertTrue('has_international_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_international_scholarship'])

        self.assertTrue('has_erasmus_mundus_scholarship' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['has_erasmus_mundus_scholarship'])

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.MASTER.name,
                'campus': EMPTY_VALUE,
                'general_education_training': 'TR1-2020',
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

    def test_general_education_form_submitting_for_a_bachelor(self):
        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.BACHELIER.name,
                'campus': EMPTY_VALUE,
            },
        )

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertTrue('general_education_training' in form.errors)
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors['general_education_training'])

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.BACHELIER.name,
                'campus': EMPTY_VALUE,
                'general_education_training': 'TR0-2020',
            },
        )

        self.mock_proposition_api.return_value.create_general_training_choice.assert_called_with(
            initier_proposition_generale_command={
                'sigle_formation': 'TR0',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'avec_bourse_double_diplome': None,
                'avec_bourse_internationale': None,
                'avec_bourse_erasmus_mundus': None,
                'bourse_double_diplome': '',
                'bourse_internationale': '',
                'bourse_erasmus_mundus': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:general-education:update:training-choice', pk=self.proposition_uuid),
        )

        self.mock_proposition_api.return_value.create_general_training_choice.reset_mock()

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.BACHELIER.name,
                'campus': EMPTY_VALUE,
                'general_education_training': 'TR0-2020',
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
                'sigle_formation': 'TR0',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'avec_bourse_double_diplome': None,
                'avec_bourse_internationale': None,
                'avec_bourse_erasmus_mundus': None,
                'bourse_double_diplome': '',
                'bourse_internationale': '',
                'bourse_erasmus_mundus': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:general-education:update:training-choice', pk=self.proposition_uuid),
        )

    def test_general_education_form_submitting_for_a_master(self):
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
                'avec_bourse_double_diplome': True,
                'avec_bourse_internationale': True,
                'avec_bourse_erasmus_mundus': True,
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
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('mixed_training', []))

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_double_degree_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_international_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('has_erasmus_mundus_scholarship', []))

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
            'has_double_degree_scholarship': True,
            'has_international_scholarship': True,
            'has_erasmus_mundus_scholarship': True,
        }

        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertFalse(form.is_valid())

        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('double_degree_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('international_scholarship', []))
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('erasmus_mundus_scholarship', []))

        data = {
            'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name,
            'campus': EMPTY_VALUE,
            'mixed_training': 'TR5-2020',
            'has_double_degree_scholarship': False,
            'has_international_scholarship': False,
            'has_erasmus_mundus_scholarship': False,
        }
        response = self.client.post(self.url, data=data)

        self.mock_proposition_api.return_value.create_general_training_choice.assert_called_with(
            initier_proposition_generale_command={
                'sigle_formation': 'TR5',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'avec_bourse_erasmus_mundus': False,
                'bourse_erasmus_mundus': '',
                'avec_bourse_double_diplome': False,
                'bourse_double_diplome': '',
                'avec_bourse_internationale': False,
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
                'admission_type': AdmissionType.PRE_ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'pre_admission_associee': '',
                'type_admission': AdmissionType.PRE_ADMISSION.name,
                'sigle_formation': 'SC3DP',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': 'Justification',
                'commission_proximite': 'MATHEMATICS',
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
                'admission_type': AdmissionType.ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'pre_admission_associee': '',
                'type_admission': AdmissionType.ADMISSION.name,
                'sigle_formation': 'TR3',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': '',
                'commission_proximite': 'ECONOMY',
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
                'admission_type': AdmissionType.ADMISSION.name,
                'justification': 'Justification',
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'pre_admission_associee': '',
                'type_admission': AdmissionType.ADMISSION.name,
                'sigle_formation': 'TR4',
                'annee_formation': 2020,
                'matricule_candidat': self.person.global_id,
                'justification': '',
                'commission_proximite': 'ECLI',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:doctorate:update:training-choice', pk=self.proposition_uuid),
        )

    def test_doctorate_education_form_initialization_after_a_pre_admission(self):
        default_choices = [('NO', _('No'))]

        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = []

        # Without pre-admissions
        response = self.client.get(self.url)

        form = response.context['form']

        self.assertEqual(form.fields['related_pre_admission'].disabled, True)
        self.assertEqual(form.fields['related_pre_admission'].choices, default_choices)

        # With pre-admissions
        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = (
            self.doctorate_pre_admissions
        )

        response = self.client.get(self.url)

        form = response.context['form']

        self.assertEqual(form.fields['related_pre_admission'].disabled, False)
        self.assertEqual(
            form.fields['related_pre_admission'].choices,
            default_choices
            + [
                (
                    current_pre_admission.uuid,
                    _('Yes, for the doctorate %(doctorate_name)s')
                    % {
                        'doctorate_name': f'{current_pre_admission.doctorat.sigle} - '
                        f'{current_pre_admission.doctorat.intitule} '
                        f'({current_pre_admission.doctorat.campus.nom})'
                    },
                )
                for current_pre_admission in self.doctorate_pre_admissions
            ],
        )

    def test_doctorate_education_form_submitting_after_a_pre_admission_with_missing_data(self):
        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = (
            self.doctorate_pre_admissions
        )

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'sector': 'SSH',
                'admission_type': AdmissionType.ADMISSION.name,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertFormError(form, 'related_pre_admission', FIELD_REQUIRED_MESSAGE)

    def test_doctorate_education_form_submitting_after_a_pre_admission_with_pre_admission_of_another_sector(self):
        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = (
            self.doctorate_pre_admissions
        )

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': EMPTY_VALUE,
                'sector': self.doctorate_pre_admissions[1].code_secteur_formation,
                'admission_type': AdmissionType.ADMISSION.name,
                'related_pre_admission': self.doctorate_pre_admissions[0].uuid,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertFormError(form, 'related_pre_admission', FIELD_REQUIRED_MESSAGE)

    def test_doctorate_education_form_submitting_after_a_pre_admission_with_pre_admission_of_another_campus(self):
        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = (
            self.doctorate_pre_admissions
        )

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': self.doctorate_pre_admissions[2].doctorat.campus.uuid,
                'sector': self.doctorate_pre_admissions[1].code_secteur_formation,
                'admission_type': AdmissionType.ADMISSION.name,
                'related_pre_admission': self.doctorate_pre_admissions[1].uuid,
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']

        self.assertEqual(form.is_valid(), False)
        self.assertFormError(form, 'related_pre_admission', FIELD_REQUIRED_MESSAGE)

    def test_doctorate_education_form_submitting_after_a_pre_admission_with_a_valid_pre_admission(self):
        self.mock_proposition_api.return_value.list_doctorate_pre_admissions.return_value = (
            self.doctorate_pre_admissions
        )

        response = self.client.post(
            self.url,
            data={
                'training_type': TypeFormation.DOCTORAT.name,
                'campus': self.doctorate_pre_admissions[1].doctorat.campus.uuid,
                'sector': self.doctorate_pre_admissions[1].code_secteur_formation,
                'admission_type': AdmissionType.ADMISSION.name,
                'related_pre_admission': self.doctorate_pre_admissions[1].uuid,
                'sigle_formation': 'TR4',
                'annee_formation': 2020,
                'science_sub_domain': 'MATHEMATICS',
                'proximity_commission_cde': 'ECONOMY',
                'proximity_commission_cdss': 'ECLI',
            },
        )

        self.assertEqual(response.status_code, 302)

        self.mock_proposition_api.return_value.create_doctorate_training_choice.assert_called_with(
            initier_proposition_command={
                'pre_admission_associee': self.doctorate_pre_admissions[1].uuid,
                'type_admission': AdmissionType.ADMISSION.name,
                'matricule_candidat': self.person.global_id,
                'sigle_formation': '',
                'annee_formation': None,
                'justification': '',
                'commission_proximite': '',
            },
            **self.default_kwargs,
        )

        self.assertRedirects(
            response,
            resolve_url('admission:doctorate:update:training-choice', pk=self.proposition_uuid),
        )
