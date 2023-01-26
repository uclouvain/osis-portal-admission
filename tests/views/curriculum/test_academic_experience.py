# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and educational schools.
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
import datetime
from unittest.mock import ANY

from django.shortcuts import resolve_url
from django.test import override_settings
from django.utils.translation import gettext
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import TypeFormation
from admission.contrib.enums.curriculum import (
    TranscriptType,
    EvaluationSystem,
    Grade,
    Result,
    TeachingTypeEnum,
)
from admission.contrib.forms import EMPTY_CHOICE
from admission.contrib.forms.curriculum import (
    EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS,
    EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS,
)
from admission.tests.views.curriculum.mixin import MixinTestCase


class CurriculumAcademicExperienceReadTestCase(MixinTestCase):
    def test_with_admission_on_reading_experience_is_loaded(self):
        response = self.client.get(
            resolve_url(
                'admission:doctorate:curriculum:educational_read',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_person_api.return_value.retrieve_educational_experience_admission.assert_called()

        # Check the context data
        experience = response.context.get('experience')

        self.assertEqual(experience, self.educational_experience)
        self.assertEqual(experience.start, 2018)
        self.assertEqual(experience.end, 2020)
        self.assertEqual(experience.linguistic_regime_name, 'Français')
        self.assertEqual(experience.education_name, 'Computer science')
        self.assertEqual(experience.institute_name, 'Institute of Technology')
        self.assertTrue(experience.evaluation_system_with_credits)

        experience_years = response.context.get('experience_years')
        self.assertEqual(len(experience_years), 3)
        self.assertEqual(experience_years[0]['academic_year'], 2020)
        self.assertEqual(experience_years[1]['academic_year'], 2019)  # Lost year
        self.assertEqual(experience_years[1]['is_enrolled'], False)  # Lost year
        self.assertEqual(experience_years[2]['academic_year'], 2018)

    def test_with_admission_on_reading_experience_without_year_is_loaded(self):
        self.educational_experience.educationalexperienceyear_set = []

        response = self.client.get(
            resolve_url(
                'admission:doctorate:curriculum:educational_read',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_person_api.return_value.retrieve_educational_experience_admission.assert_called()

        # Check the context data
        experience = response.context.get('experience')

        self.assertEqual(experience, self.educational_experience)
        self.assertEqual(experience.start, None)
        self.assertEqual(experience.end, None)
        self.assertEqual(experience.linguistic_regime_name, 'Français')
        self.assertEqual(experience.education_name, 'Computer science')
        self.assertTrue(experience.evaluation_system_with_credits)

        experience_years = response.context.get('experience_years')
        self.assertEqual(len(experience_years), 0)


@override_settings(SERVER_NAME=None)
class CurriculumAcademicExperienceDeleteTestCase(MixinTestCase):
    def test_with_admission_on_delete_experience_post_form(self):
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:educational_delete',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            ),
            data={
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.destroy_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            **self.api_default_params,
        )

    def test_with_admission_on_delete_valuated_experience_is_forbidden(self):
        mock_retrieve = self.mock_person_api.return_value.retrieve_educational_experience_admission
        mock_retrieve.return_value.valuated_from_trainings = [TypeFormation.DOCTORAT.name]

        response = self.client.get(
            resolve_url(
                'admission:doctorate:update:curriculum:educational_delete',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_without_admission_on_delete_experience_form_is_not_initialized(self):
        response = self.client.get(
            resolve_url(
                'admission:create:curriculum:educational_delete',
                experience_id=self.educational_experience.uuid,
            )
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.retrieve_educational_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )


class CurriculumAcademicExperienceFormTestCase(MixinTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.all_form_data = {
            'base_form-start': '2018',
            'base_form-end': '2020',
            'base_form-country': cls.be_country.iso_code,
            'base_form-other_institute': True,
            'base_form-institute_name': 'UCL',
            'base_form-institute_address': 'Louvain-La-Neuve',
            'base_form-institute': cls.institute.uuid,
            'base_form-program': cls.first_diploma.uuid,
            'base_form-other_program': True,
            'base_form-education_name': 'Other computer science',
            'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
            'base_form-linguistic_regime': cls.language_with_translation.code,
            'base_form-transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
            'base_form-obtained_diploma': True,
            'base_form-obtained_grade': Grade.GREAT_DISTINCTION.name,
            'base_form-graduate_degree_0': ['f1.pdf'],
            'base_form-graduate_degree_translation_0': ['f11.pdf'],
            'base_form-transcript_0': ['f2.pdf'],
            'base_form-transcript_translation_0': ['f22.pdf'],
            'base_form-rank_in_diploma': '10 on 100',
            'base_form-expected_graduation_date': datetime.date(2022, 1, 1),
            'base_form-dissertation_title': 'The new title',
            'base_form-dissertation_score': 'A',
            'base_form-dissertation_summary_0': ['f3.pdf'],
            'year_formset-2018-is_enrolled': True,
            'year_formset-2018-academic_year': '2018',
            'year_formset-2018-result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
            'year_formset-2018-acquired_credit_number': 100,
            'year_formset-2018-registered_credit_number': 150,
            'year_formset-2018-transcript_0': ['f1_2018.pdf'],
            'year_formset-2018-transcript_translation_0': ['f11_2018.pdf'],
            'year_formset-2019-is_enrolled': False,
            'year_formset-2019-academic_year': '2019',
            'year_formset-2019-acquired_credit_number': 100,
            'year_formset-2019-registered_credit_number': 150,
            'year_formset-2019-result': Result.WAITING_RESULT.name,
            'year_formset-2019-transcript_0': ['f1_2019.pdf'],
            'year_formset-2019-transcript_translation_0': ['f11_2019.pdf'],
            'year_formset-2020-is_enrolled': True,
            'year_formset-2020-academic_year': '2020',
            'year_formset-2020-acquired_credit_number': 100,
            'year_formset-2020-registered_credit_number': 150,
            'year_formset-2020-result': Result.SUCCESS.name,
            'year_formset-2020-transcript_0': ['f1_2020.pdf'],
            'year_formset-2020-transcript_translation_0': ['f11_2020.pdf'],
            'year_formset-TOTAL_FORMS': '3',
            'year_formset-INITIAL_FORMS': '3',
            '_submit_and_continue': True,
        }

    def setUp(self):
        super().setUp()
        self.admission_update_url = resolve_url(
            'admission:doctorate:update:curriculum:educational_update',
            pk=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
        )
        self.without_admission_update_url = resolve_url(
            'admission:create:curriculum:educational_update',
            experience_id=self.educational_experience.uuid,
        )
        self.general_admission_update_url = resolve_url(
            'admission:general-education:update:curriculum:educational_update',
            pk=self.general_proposition.uuid,
            experience_id=self.educational_experience.uuid,
        )
        self.continuing_admission_update_url = resolve_url(
            'admission:continuing-education:update:curriculum:educational_update',
            pk=self.continuing_proposition.uuid,
            experience_id=self.educational_experience.uuid,
        )
        self.mockapi = self.mock_person_api.return_value

    # On update
    def test_with_admission_on_update_experience_form_is_initialized(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_educational_experience_admission.assert_called()

        # Check the context data
        # Base form
        base_form = response.context.get('base_form')
        self.assertEqual(
            base_form.initial,
            {
                'country': self.be_country.iso_code,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'institute': self.institute.uuid,
                'institute_name': 'UCL',
                'institute_address': "Place de l'Université",
                'program': self.first_diploma.uuid,
                'education_name': 'Other computer science',
                'study_system': TeachingTypeEnum.FULL_TIME.name,
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': self.language_without_translation.code,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': ['f11.pdf'],
                'transcript': ['f2.pdf'],
                'transcript_translation': ['f22.pdf'],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 8, 30),
                'dissertation_title': 'Title',
                'dissertation_score': '15/20',
                'dissertation_summary': [self.document_uuid],
                'uuid': self.educational_experience.uuid,
                'start': 2018,
                'end': 2020,
                'other_program': True,
                'other_institute': True,
                'can_be_updated': ANY,
                'valuated_from_trainings': ANY,
            },
        )
        # Check the choices of the fields
        self.assertEqual(
            base_form.fields['start'].choices,
            [EMPTY_CHOICE[0]]
            + [
                (2018, '2018-2019'),
                (2019, '2019-2020'),
                (2020, '2020-2021'),
                (2021, '2021-2022'),
                (2022, '2022-2023'),
            ],
        )
        self.assertEqual(
            base_form.fields['end'].choices,
            base_form.fields['start'].choices,
        )
        self.assertEqual(
            base_form.fields['country'].widget.choices,
            EMPTY_CHOICE + ((self.be_country.iso_code, self.be_country.name),),
        )
        self.assertTrue(base_form.fields['country'].is_ue_country)
        self.assertEqual(
            base_form.fields['linguistic_regime'].widget.choices,
            EMPTY_CHOICE + ((self.language_without_translation.code, self.language_without_translation.name),),
        )
        self.assertEqual(
            base_form.fields['program'].widget.choices,
            EMPTY_CHOICE + ((self.first_diploma.uuid, self.first_diploma.title),),
        )
        self.assertEqual(
            base_form.fields['institute'].widget.choices,
            EMPTY_CHOICE + ((self.institute.uuid, self.institute.name),),
        )

        # Check that no field is hidden or disabled
        self.assertEqual(len(base_form.hidden_fields()), 0)
        for f in base_form.fields:
            self.assertFalse(base_form.fields[f].disabled)

        # Check formset
        year_formset = response.context.get('year_formset')
        forms = year_formset.forms
        self.assertEqual(len(forms), 3)
        self.assertEqual(
            forms[0].initial,
            {
                'academic_year': 2020,
                'graduate_degree': ['f1_2020.pdf'],
                'graduate_degree_translation': ['f11_2020.pdf'],
                'result': Result.SUCCESS.name,
            },
        )
        self.assertEqual(
            forms[1].initial,
            {
                'academic_year': 2019,
                'is_enrolled': False,
            },
        )
        self.assertEqual(
            forms[2].initial,
            {
                'academic_year': 2018,
                'graduate_degree': ['f1_2018.pdf'],
                'graduate_degree_translation': ['f11_2018.pdf'],
                'result': Result.SUCCESS.name,
            },
        )

    def test_with_admission_on_update_experience_form_is_forbidden_with_doctorate_and_valuated_by_doctorate(self):
        # Valuated by a doctorate admission
        self.mockapi.retrieve_educational_experience_admission.return_value.valuated_from_trainings = [
            TypeFormation.DOCTORAT.name,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_with_admission_on_update_experience_form_is_initialized_with_doctorate_and_valuated_by_general(self):
        editable_fields = EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS
        self.mockapi.retrieve_educational_experience_admission.return_value.valuated_from_trainings = [
            TypeFormation.MASTER.name,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the context data
        base_form = response.context.get('base_form')

        # Check that the right fields are disabled
        for f in base_form.fields:
            self.assertEqual(f not in editable_fields, base_form.fields[f].disabled)

    def test_with_admission_on_update_experience_form_is_initialized_with_doctorate_and_valuated_by_continuing(self):
        editable_fields = EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS
        self.mockapi.retrieve_educational_experience_admission.return_value.valuated_from_trainings = [
            TypeFormation.FORMATION_CONTINUE.name,
        ]

        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the context data
        base_form = response.context.get('base_form')

        # Check that the right fields are disabled
        for f in base_form.fields:
            self.assertEqual(f not in editable_fields, base_form.fields[f].disabled)

    def test_with_admission_on_update_experience_form_is_initialized_with_general_education(self):
        response = self.client.get(self.general_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_educational_experience_general_education_admission.assert_called()

        # Check the context data
        base_form = response.context.get('base_form')
        non_visible_fields = [base_form.fields[field] for field in EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS]
        for field in non_visible_fields:
            self.assertTrue(field.disabled)

        self.assertCountEqual([f.field for f in base_form.hidden_fields()], non_visible_fields)

    def test_with_admission_on_update_experience_form_is_forbidden_with_general_and_valuated_by_doctorate(self):
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_general_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.DOCTORAT.name,
        ]

        response = self.client.get(self.general_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_with_admission_on_update_experience_form_is_forbidden_with_general_and_valuated_by_general(self):
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_general_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.MASTER.name,
        ]

        response = self.client.get(self.general_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_with_admission_on_update_experience_form_is_initialized_with_general_and_valuated_by_continuing(self):
        editable_fields = EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_general_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.FORMATION_CONTINUE.name,
        ]

        response = self.client.get(self.general_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check the context data
        base_form = response.context.get('base_form')

        # Check that the right fields are disabled
        for f in base_form.fields:
            self.assertEqual(f not in editable_fields, base_form.fields[f].disabled)

    def test_with_admission_on_update_experience_form_is_initialized_with_continuing_education(self):
        response = self.client.get(self.continuing_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_educational_experience_continuing_education_admission.assert_called()

        # Check the context data
        base_form = response.context.get('base_form')

        non_visible_fields = [
            base_form.fields[field]
            for field in EDUCATIONAL_EXPERIENCE_DOCTORATE_FIELDS | EDUCATIONAL_EXPERIENCE_GENERAL_FIELDS
        ]
        for field in non_visible_fields:
            self.assertTrue(field.disabled)

        self.assertCountEqual([f.field for f in base_form.hidden_fields()], non_visible_fields)

    def test_with_admission_on_update_experience_form_is_forbidden_with_continuing_and_valuated_by_doctorate(self):
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_continuing_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.DOCTORAT.name,
        ]

        response = self.client.get(self.continuing_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_with_admission_on_update_experience_form_is_forbidden_with_continuing_and_valuated_by_general(self):
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_continuing_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.MASTER.name,
        ]

        response = self.client.get(self.continuing_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_with_admission_on_update_experience_form_is_forbidden_with_continuing_and_valuated_by_continuing(self):
        mock_retrieve_experience = self.mockapi.retrieve_educational_experience_continuing_education_admission
        mock_retrieve_experience.return_value.valuated_from_trainings = [
            TypeFormation.FORMATION_CONTINUE.name,
        ]

        response = self.client.get(self.continuing_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    def test_without_admission_on_update_experience_form_is_not_initialized(self):
        response = self.client.get(self.without_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.retrieve_educational_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )

    def test_with_admission_on_update_experience_post_form_empty_data(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'unknown_field': '',
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['base_form'].errors), 8)
        for field in ['start', 'end', 'country', 'evaluation_type', 'transcript_type', 'obtained_diploma', 'institute']:
            self.assertFormError(response, 'base_form', field, errors=FIELD_REQUIRED_MESSAGE)

        self.assertFormError(response, 'base_form', None, errors=gettext('At least one academic year is required.'))

    def test_with_admission_on_update_experience_post_form_bad_dates(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-start': '2020',
                'base_form-end': '2019',
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(
            response,
            'base_form',
            None,
            errors=gettext("The start date must be equals or lower than the end date."),
        )

    def test_with_admission_on_update_experience_post_form_missing_other_institute(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-other_institute': True,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        for field in ['institute_name', 'institute_address']:
            self.assertFormError(response, 'base_form', field, FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_missing_obtained_diploma_information(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-obtained_diploma': True,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        for field in [
            'obtained_grade',
            'expected_graduation_date',
            'dissertation_title',
            'dissertation_score',
        ]:
            self.assertFormError(response, 'base_form', field, FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_for_be_missing_other_program(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-country': self.be_country.iso_code,
                'base_form-other_program': True,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(response, 'base_form', 'education_name', FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_for_be_missing_program(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-country': self.be_country.iso_code,
                'base_form-other_program': False,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(response, 'base_form', 'program', FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_for_foreign_country_missing_fields(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-country': self.not_ue_country.iso_code,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(response, 'base_form', 'education_name', FIELD_REQUIRED_MESSAGE)
        self.assertFormError(response, 'base_form', 'linguistic_regime', FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_for_foreign_country_missing_fields_for_enrolled_year(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-start': '2020',
                'base_form-end': '2020',
                'base_form-country': self.not_ue_country.iso_code,
                'base_form-evaluation_type': EvaluationSystem.NON_EUROPEAN_CREDITS.name,
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-linguistic_regime': self.language_with_translation.code,
                'year_formset-2020-is_enrolled': True,
                'year_formset-2020-academic_year': '2020',
                'year_formset-TOTAL_FORMS': '1',
                'year_formset-INITIAL_FORMS': '0',
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        # Check the context data
        for field in [
            'acquired_credit_number',
            'registered_credit_number',
            'result',
        ]:
            self.assertFormsetError(response, 'year_formset', 0, field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_for_be_country_invalid_credits_for_required_years(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'base_form-start': '2003',
                'base_form-end': '2006',
                'base_form-country': self.be_country.iso_code,
                'base_form-evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'year_formset-2003-is_enrolled': True,
                'year_formset-2003-academic_year': '2003',
                'year_formset-2004-is_enrolled': True,
                'year_formset-2004-academic_year': '2004',
                'year_formset-2005-is_enrolled': True,
                'year_formset-2005-academic_year': '2005',
                'year_formset-2005-acquired_credit_number': 100,
                'year_formset-2005-registered_credit_number': 99,
                'year_formset-2006-is_enrolled': True,
                'year_formset-2006-academic_year': '2006',
                'year_formset-2006-acquired_credit_number': -1,
                'year_formset-2006-registered_credit_number': 0,
                'year_formset-TOTAL_FORMS': '4',
                'year_formset-INITIAL_FORMS': '0',
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_educational_experience_admission.assert_not_called()

        forms = response.context['year_formset'].forms
        self.assertEqual(len(forms), 4)

        forms_by_year = {form.cleaned_data['academic_year']: form for form in forms}

        # Check the context data
        for field in [
            'acquired_credit_number',
            'registered_credit_number',
        ]:
            # Before 2004, the credits are not required
            self.assertNotIn(FIELD_REQUIRED_MESSAGE, forms_by_year[2003].errors.get(field, []))
            # From 2004, the credits are required
            self.assertIn(FIELD_REQUIRED_MESSAGE, forms_by_year[2004].errors.get(field, []))

        # Check the number limits
        self.assertIn(
            gettext('This value cannot be greater than the entered credits number'),
            forms_by_year[2005].errors.get('acquired_credit_number', []),
        )
        self.assertIn(
            gettext('This value must be greater than %(MINIMUM_CREDIT_NUMBER)s') % {'MINIMUM_CREDIT_NUMBER': 0},
            forms_by_year[2006].errors.get('registered_credit_number', []),
        )
        self.assertIn(
            gettext('This value must be equal to or greater than %(MINIMUM_CREDIT_NUMBER)s')
            % {'MINIMUM_CREDIT_NUMBER': 0},
            forms_by_year[2006].errors.get('acquired_credit_number', []),
        )

    def test_with_admission_on_update_experience_post_form_for_be_country(self):
        response = self.client.post(
            self.admission_update_url,
            data=self.all_form_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': 'BE',
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': None,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': [],
                'transcript': ['f2.pdf'],
                'transcript_translation': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 1, 1),
                'dissertation_title': 'The new title',
                'dissertation_score': 'A',
                'dissertation_summary': ['f3.pdf'],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_be_country_general_education(self):
        response = self.client.post(
            self.general_admission_update_url,
            data=self.all_form_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:general-education:update:curriculum', pk=self.general_proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_general_education_admission.assert_called_once_with(
            uuid=self.general_proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': 'BE',
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': None,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': [],
                'transcript': ['f2.pdf'],
                'transcript_translation': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 8, 30),
                'dissertation_title': 'Title',
                'dissertation_score': '15/20',
                'dissertation_summary': ['foobar'],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_be_country_continuing_education(self):
        response = self.client.post(
            self.continuing_admission_update_url,
            data=self.all_form_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:update:curriculum',
                pk=self.continuing_proposition.uuid,
            )
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_continuing_education_admission.assert_called_once_with(
            uuid=self.continuing_proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': 'BE',
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': None,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': [],
                'transcript': ['f2.pdf'],
                'transcript_translation': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 8, 30),
                'dissertation_title': 'Title',
                'dissertation_score': '15/20',
                'dissertation_summary': ['foobar'],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': 'SUCCESS',
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': 'SUCCESS',
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_be_country_known_program(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'base_form-other_program': False,
                'base_form-other_institute': False,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': 'BE',
                'institute_name': '',
                'institute_address': '',
                'institute': self.institute.uuid,
                'program': self.first_diploma.uuid,
                'education_name': '',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': None,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': [],
                'transcript': ['f2.pdf'],
                'transcript_translation': [],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 1, 1),
                'dissertation_title': 'The new title',
                'dissertation_score': 'A',
                'dissertation_summary': ['f3.pdf'],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_foreign_country_with_translation(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'base_form-country': self.not_ue_country.iso_code,
                'base_form-obtained_diploma': False,
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-evaluation_type': EvaluationSystem.NO_CREDIT_SYSTEM.name,
                'year_formset-2018-result': Result.FAILURE.name,
                'year_formset-2019-result': Result.WAITING_RESULT.name,
                'year_formset-2020-result': Result.WAITING_RESULT.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': self.not_ue_country.iso_code,
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.NO_CREDIT_SYSTEM.name,
                'linguistic_regime': self.language_with_translation.code,
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
                'obtained_diploma': False,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': [],
                'graduate_degree_translation': [],
                'transcript': [],
                'transcript_translation': [],
                'rank_in_diploma': '',
                'expected_graduation_date': None,
                'dissertation_title': '',
                'dissertation_score': '',
                'dissertation_summary': [],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.WAITING_RESULT.name,
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': ['f1_2020.pdf'],
                        'transcript_translation': ['f11_2020.pdf'],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.FAILURE.name,
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': ['f1_2018.pdf'],
                        'transcript_translation': ['f11_2018.pdf'],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_foreign_country_without_translation(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'base_form-country': self.not_ue_country.iso_code,
                'base_form-linguistic_regime': self.language_without_translation.code,
                'base_form-obtained_diploma': False,
                'base_form-transcript_type': TranscriptType.ONE_A_YEAR.name,
                'base_form-evaluation_type': EvaluationSystem.NO_CREDIT_SYSTEM.name,
                'year_formset-2018-result': Result.FAILURE.name,
                'year_formset-2019-result': Result.WAITING_RESULT.name,
                'year_formset-2020-result': Result.WAITING_RESULT.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': self.not_ue_country.iso_code,
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.NO_CREDIT_SYSTEM.name,
                'linguistic_regime': self.language_without_translation.code,
                'transcript_type': TranscriptType.ONE_A_YEAR.name,
                'obtained_diploma': False,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': [],
                'graduate_degree_translation': [],
                'transcript': [],
                'transcript_translation': [],
                'rank_in_diploma': '',
                'expected_graduation_date': None,
                'dissertation_title': '',
                'dissertation_score': '',
                'dissertation_summary': [],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.WAITING_RESULT.name,
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': ['f1_2020.pdf'],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.FAILURE.name,
                        'registered_credit_number': None,
                        'acquired_credit_number': None,
                        'transcript': ['f1_2018.pdf'],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_foreign_country_graduated_with_translation(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'base_form-country': self.not_ue_country.iso_code,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.educational_experience.uuid,
            educational_experience={
                'start': '2018',
                'end': '2020',
                'country': self.not_ue_country.iso_code,
                'institute_name': 'UCL',
                'institute_address': 'Louvain-La-Neuve',
                'institute': None,
                'program': None,
                'education_name': 'Other computer science',
                'evaluation_type': EvaluationSystem.ECTS_CREDITS.name,
                'linguistic_regime': self.language_with_translation.code,
                'transcript_type': TranscriptType.ONE_FOR_ALL_YEARS.name,
                'obtained_diploma': True,
                'obtained_grade': Grade.GREAT_DISTINCTION.name,
                'graduate_degree': ['f1.pdf'],
                'graduate_degree_translation': ['f11.pdf'],
                'transcript': ['f2.pdf'],
                'transcript_translation': ['f22.pdf'],
                'rank_in_diploma': '10 on 100',
                'expected_graduation_date': datetime.date(2022, 1, 1),
                'dissertation_title': 'The new title',
                'dissertation_score': 'A',
                'dissertation_summary': ['f3.pdf'],
                'educationalexperienceyear_set': [
                    {
                        'academic_year': 2020,
                        'result': Result.SUCCESS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                    {
                        'academic_year': 2018,
                        'result': Result.SUCCESS_WITH_RESIDUAL_CREDITS.name,
                        'registered_credit_number': 150.0,
                        'acquired_credit_number': 100.0,
                        'transcript': [],
                        'transcript_translation': [],
                    },
                ],
            },
            **self.api_default_params,
        )

    # On create
    def test_with_admission_on_create_experience_post_form_for_be_country(self):
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:educational_create',
                pk=self.proposition.uuid,
            ),
            data=self.all_form_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.create_educational_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            educational_experience=ANY,
            **self.api_default_params,
        )

    def test_with_admission_on_create_experience_post_form_for_be_country_and_redirect_to_editing_page(self):
        self.mockapi.create_educational_experience_admission.return_value = {
            'uuid': self.educational_experience.uuid,
        }

        all_form_data = self.all_form_data.copy()
        all_form_data.pop('_submit_and_continue')
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:educational_create',
                pk=self.proposition.uuid,
            ),
            data=all_form_data,
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:doctorate:update:curriculum:educational_update',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
            + '#curriculum-header',
        )

    def test_without_admission_on_create_experience_form_is_not_initialized(self):
        response = self.client.get(
            resolve_url('admission:create:curriculum:educational_create'),
            data=self.all_form_data,
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.retrieve_educational_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )
