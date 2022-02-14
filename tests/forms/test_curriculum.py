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
import datetime
from unittest.mock import patch, Mock

from django.conf import settings
from django.test import TestCase
from django.utils.translation import get_language

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.curriculum import ExperienceType, Result, Grade, CreditType, StudySystem, \
    ForeignStudyCycleType, ActivityType
from admission.contrib.enums.secondary_studies import BelgianCommunitiesOfEducation
from admission.contrib.forms.curriculum import DoctorateAdmissionCurriculumExperienceForm
from admission.tests.utils import MockCountry, MockLanguage
from base.tests.factories.person import PersonFactory


class CurriculumFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        cls.is_supported_language = get_language() == settings.LANGUAGE_CODE

    def setUp(self):
        # Mock countries api
        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        def get_countries(**kwargs):
            countries = [
                MockCountry(iso_code='FR', name='France', name_en='France'),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium'),
            ]
            if kwargs.get('iso_code'):
                return Mock(results=[c for c in countries if c.iso_code == kwargs.get('iso_code')])
            return Mock(results=countries)

        self.mock_countries_api.return_value.countries_list.side_effect = get_countries
        self.addCleanup(countries_api_patcher.stop)

        # Mock languages api
        languages_api_patcher = patch("osis_reference_sdk.api.languages_api.LanguagesApi")
        self.mock_languages_api = languages_api_patcher.start()

        def get_languages(**kwargs):
            languages = [
                MockLanguage(code='FR', name='Français', name_en='French'),
                MockLanguage(code='EN', name='Anglais', name_en='English'),
                MockLanguage(code='AR', name='Arabe', name_en='Arabic'),
            ]
            if kwargs.get('code'):
                return Mock(results=[c for c in languages if c.code == kwargs.get('code')])
            return Mock(results=languages)

        self.mock_languages_api.return_value.languages_list.side_effect = get_languages
        self.addCleanup(languages_api_patcher.stop)

        # Mock academic year api
        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.current_year = datetime.date.today().year

        def get_academic_years(**kwargs):
            years = [
                Mock(year=self.current_year-2),
                Mock(year=self.current_year+2),
            ]
            return Mock(results=years)
        self.mock_academic_year_api.return_value.get_academic_years.side_effect = get_academic_years
        self.addCleanup(academic_year_api_patcher.stop)

        # Mock document api
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_curriculum_form_initialization_with_empty_experience(self):
        form = DoctorateAdmissionCurriculumExperienceForm(
            initial={
                'a': 1,
            },
            person=self.person,
        )

        # Check that the choices are well initialized
        self.assertIn(
            (self.current_year - 2, '{}-{}'.format(self.current_year - 2, (self.current_year - 1) % 100)),
            form.fields['academic_year'].choices,
        )

    def test_curriculum_form_initialization_with_full_experience(self):
        experience = {
            'curriculum_year': {
                'academic_year': 2020,
                'id': 1,
            },
            'country': BE_ISO_CODE,
            'program': None,
            'institute': None,
            'is_valuated': False,
            'linguistic_regime': 'FR',
            'type': ExperienceType.HIGHER_EDUCATION.name,
            'institute_name': 'UCL',
            'institute_city': 'Louvain-La-Neuve',
            'institute_postal_code': '1348',
            'education_name': 'IT',
            'result': Result.SUCCESS.name,
            'graduation_year': True,
            'obtained_grade': Grade.DISTINCTION.name,
            'rank_in_diploma': 'top 20',
            'issue_diploma_date': '2021-09-01',
            'credit_type': CreditType.EUROPEAN_UNION_CREDITS.name,
            'entered_credits_number': 180,
            'acquired_credits_number': 180,
            'dissertation_title': 'IoT',
            'dissertation_score': 14.2,
            'belgian_education_community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            'study_system': StudySystem.FULL_TIME_EDUCATION.name,
            'study_cycle_type': ForeignStudyCycleType.MASTER.name,
            'activity_type': ActivityType.WORK.name,
            'other_activity_type': 'Other activity',
            'activity_position': 'Activity position',
        }

        form = DoctorateAdmissionCurriculumExperienceForm(
            initial=experience,
            person=self.person,
        )

        # Check that the fields which are not automatically mapping are well initialized
        self.assertEqual(form.initial['academic_year'], 2020)
        self.assertEqual(form.initial['linguistic_regime'], 'FR')
        self.assertEqual(form.initial['other_program'], 'IT')
        self.assertEqual(form.initial['program_not_found'], True)
        self.assertEqual(form.initial['institute_not_found'], True)
        self.assertEqual(form.initial['institute_city_be'], 'Louvain-La-Neuve')
        self.assertEqual(form.initial['activity_institute_city'], 'Louvain-La-Neuve')
        self.assertEqual(form.initial['activity_institute_name'], 'UCL')

        # Check that the choices are well initialized
        self.assertIn(
            (BE_ISO_CODE, 'Belgique' if self.is_supported_language else 'Belgium'),
            form.fields['country'].widget.choices,
        )
        self.assertIn(
            ('FR', 'Français' if self.is_supported_language else 'French'),
            form.fields['linguistic_regime'].widget.choices,
        )
        self.assertIn(
            ('Louvain-La-Neuve', 'Louvain-La-Neuve'),
            form.fields['institute_city_be'].widget.choices,
        )
        self.assertIn(
            (self.current_year - 2, '{}-{}'.format(self.current_year - 2, (self.current_year - 1) % 100)),
            form.fields['academic_year'].choices,
        )

    def test_curriculum_form_validation_with_belgian_studies_field_initialization(self):
        experience = {
            'academic_year': 2020,
            'country': BE_ISO_CODE,
            'type': ExperienceType.HIGHER_EDUCATION.name,
            'institute_name': 'UCL',
            'institute_postal_code': '1348',
            'result': Result.SUCCESS.name,
            'graduation_year': True,
            'obtained_grade': Grade.DISTINCTION.name,
            'rank_in_diploma': 'top 20',
            'issue_diploma_date': '2021-09-01',
            'credit_type': CreditType.EUROPEAN_UNION_CREDITS.name,
            'entered_credits_number': 180,
            'acquired_credits_number': 180,
            'dissertation_title': 'IoT',
            'dissertation_score': 14.2,
            'dissertation_summary_0': 'uuid1',
            'belgian_education_community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            'study_system': StudySystem.FULL_TIME_EDUCATION.name,
            'program_not_found': True,
            'other_program': 'BE-IT',
            'institute_not_found': True,
            'institute_city_be': 'Louvain-La-Neuve',
        }

        form = DoctorateAdmissionCurriculumExperienceForm(
            data=experience,
            person=self.person,
        )

        self.assertTrue(form.is_valid())

        # Check that the fields which are not automatically mapping are well saved
        self.assertEqual(form.cleaned_data['institute_city'], 'Louvain-La-Neuve')
        self.assertEqual(form.cleaned_data['education_name'], 'BE-IT')

    def test_curriculum_form_validation_required_fields(self):
        # Check the fields that we have to specify by default with a belgian education
        form = DoctorateAdmissionCurriculumExperienceForm(
            data={},
            person=self.person,
        )

        required_fields = [
            'academic_year',
            'country',
            'type',
        ]

        self.assertFalse(form.is_valid())

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

    def test_curriculum_form_validation_with_belgian_studies_required_fields(self):
        default_required_fields = [
            'acquired_credits_number',
            'credit_type',
            'dissertation_score',
            'dissertation_summary',
            'dissertation_title',
            'entered_credits_number',
            'study_system',
        ]

        # Check the fields that we have to specify by default with a belgian education
        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': BE_ISO_CODE,
                'type': ExperienceType.HIGHER_EDUCATION.name,
            },
            person=self.person,
        )

        required_fields = default_required_fields + [
            'belgian_education_community',
            'institute',
            'result',
        ]

        self.assertFalse(form.is_valid())

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': BE_ISO_CODE,
                'type': ExperienceType.HIGHER_EDUCATION.name,
                # Specificities
                'belgian_education_community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                'institute_not_found': True,
                'program_not_found': True,
                'result': Result.NO_RESULT.name,
            },
            person=self.person,
        )

        required_fields = default_required_fields + [
            'institute_city_be',
            'institute_name',
            'institute_postal_code',
            'other_program',
        ]

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': BE_ISO_CODE,
                'type': ExperienceType.HIGHER_EDUCATION.name,
                # Specificities
                'belgian_education_community': BelgianCommunitiesOfEducation.GERMAN_SPEAKING.name,
                'graduation_year': True,
                'result': Result.SUCCESS.name,
            },
            person=self.person,
        )

        required_fields = default_required_fields + [
            'education_name',
            'institute',
            'obtained_grade',
        ]

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': BE_ISO_CODE,
                'type': ExperienceType.HIGHER_EDUCATION.name,
                # Specificities
                'belgian_education_community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                'result': Result.SUCCESS.name,
            },
            person=self.person,
        )

        required_fields = default_required_fields + [
            'institute',
            'program',
        ]

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

    def test_curriculum_form_validation_with_foreign_studies_choice_initialization(self):
        experience = {
            'academic_year': 2020,
            'country': 'FR',
            'type': ExperienceType.HIGHER_EDUCATION.name,
            'institute_name': 'Institute name',
            'institute_postal_code': '44000',
            'institute_city': 'Nantes',
            'result': Result.SUCCESS.name,
            'graduation_year': True,
            'obtained_grade': Grade.DISTINCTION.name,
            'rank_in_diploma': 'top 20',
            'issue_diploma_date': '2021-09-01',
            'credit_type': CreditType.EUROPEAN_UNION_CREDITS.name,
            'entered_credits_number': 180,
            'acquired_credits_number': 180,
            'dissertation_title': 'IoT',
            'dissertation_score': 14.2,
            'dissertation_summary_0': 'uuid1',
            'institute_not_found': True,
            'linguistic_regime': 'FR',
            'study_cycle_type': ForeignStudyCycleType.MASTER.name,
            'education_name': 'IT',
        }

        form = DoctorateAdmissionCurriculumExperienceForm(
            data=experience,
            person=self.person,
        )

        self.assertTrue(form.is_valid())

        # Check that the choices are well initialized
        self.assertIn(
            ('FR', 'France'),
            form.fields['country'].widget.choices,
        )
        self.assertIn(
            ('FR', 'Français' if self.is_supported_language else 'French'),
            form.fields['linguistic_regime'].widget.choices,
        )
        self.assertIn(
            (self.current_year - 2, '{}-{}'.format(self.current_year - 2, (self.current_year - 1) % 100)),
            form.fields['academic_year'].choices,
        )

    def test_curriculum_form_validation_with_foreign_studies_required_fields(self):
        default_required_fields = [
            'acquired_credits_number',
            'credit_type',
            'dissertation_score',
            'dissertation_summary',
            'dissertation_title',
            'education_name',
            'entered_credits_number',
            'linguistic_regime',
            'result',
        ]

        # Check the fields that we have to specify by default with a foreign education
        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': 'FR',
                'type': ExperienceType.HIGHER_EDUCATION.name,
            },
            person=self.person,
        )

        required_fields = default_required_fields + [
            'institute',
            'study_cycle_type',
        ]

        self.assertFalse(form.is_valid())

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': 'FR',
                'type': ExperienceType.HIGHER_EDUCATION.name,
                # Specificities
                'study_cycle_type': ForeignStudyCycleType.OTHER_HIGHER_EDUCATION.name,
            },
            person=self.person,
        )

        for f in default_required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(default_required_fields))

    def test_curriculum_form_validation_with_other_activity_field_initialization(self, *args):
        experience = {
            'academic_year': 2020,
            'country': BE_ISO_CODE,
            'type': ExperienceType.OTHER_ACTIVITY.name,
            'activity_institute_name': 'UCL',
            'activity_institute_city': 'Louvain-La-Neuve',
            'activity_type': ActivityType.WORK.name,
            'activity_certificate_0': 'uuid1',
        }

        form = DoctorateAdmissionCurriculumExperienceForm(
            data=experience,
            person=self.person,
        )

        self.assertTrue(form.is_valid())

        # Check that the fields which are not automatically mapping are well saved
        self.assertEqual(form.cleaned_data['institute_city'], 'Louvain-La-Neuve')
        self.assertEqual(form.cleaned_data['institute_name'], 'UCL')

    def test_curriculum_form_validation_with_other_activity_required_fields(self):
        # Check the fields that we have to specify by default with a non-education experience
        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': 'FR',
                'type': ExperienceType.OTHER_ACTIVITY.name,
            },
            person=self.person,
        )

        self.assertFalse(form.is_valid())

        required_fields = [
            'activity_certificate',
            'activity_type',
        ]

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))

        form = DoctorateAdmissionCurriculumExperienceForm(
            data={
                'academic_year': 2020,
                'country': 'FR',
                'type': ExperienceType.OTHER_ACTIVITY.name,
                # Specificities
                'activity_type': ActivityType.OTHER.name,
            },
            person=self.person,
        )

        required_fields = [
            'activity_certificate',
            'activity_institute_city',
            'other_activity_type',
        ]

        for f in required_fields:
            self.assertIn(f, form.errors)

        self.assertEqual(len(form.errors), len(required_fields))
