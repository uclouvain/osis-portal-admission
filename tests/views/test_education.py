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
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    DiplomaTypes,
    EducationalType, Equivalence, ForeignDiplomaTypes, GotDiploma,
)
from admission.tests.utils import MockCountry, MockLanguage
from base.tests.factories.academic_year import get_current_year
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class EducationTestCase(TestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.detail_url = resolve_url('admission:doctorate-detail:education', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        cls.form_url = resolve_url('admission:doctorate-create:education')

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        person_api_ret = self.mock_person_api.return_value
        default_return = {
            'belgian_diploma': None,
            'foreign_diploma': None,
        }
        person_api_ret.retrieve_high_school_diploma.return_value.to_dict.return_value \
            = person_api_ret.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = default_return
        self.addCleanup(person_api_patcher.stop)

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

        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

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

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.addCleanup(academic_year_api_patcher.stop)

    def test_form_empty(self):
        response = self.client.get(self.form_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.retrieve_high_school_diploma.assert_called()
        self.mock_proposition_api.assert_not_called()

        response = self.client.post(self.form_url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(sent, {})

    def test_form_belgian(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.BELGIAN.name,
            "high_school_transcript_0": "test",
            "high_school_diploma_0": "test",
            "academic_graduation_year": 2020,
            "belgian_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            "belgian_diploma-community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
            "belgian_diploma-other_institute": "Special school",
            # Even if we send data for schedule, it should be stripped from data sent to WS
            "schedule-greek": 5,
            # Even if we send data for foreign diploma, it should be stripped from data sent to WS
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(sent, {
            'belgian_diploma': {
                'academic_graduation_year': 2020,
                'community': BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                "high_school_transcript": ["test"],
                "high_school_diploma": ["test"],
                'educational_other': '',
                'educational_type': '',
                'institute': '',
                'other_institute': 'Special school',
                'result': DiplomaResults.NOT_KNOWN_YET_RESULT.name
            },
        })

    def test_form_belgian_schedule(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.BELGIAN.name,
            "academic_graduation_year": 2020,
            "high_school_transcript_0": "test",
            "high_school_diploma_0": "test",
            "belgian_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
            "belgian_diploma-other_institute": "Special school",
            "schedule-latin": 5,
            "schedule-chemistry": 5,
            "schedule-physic": 5,
            "schedule-biology": 5,
            "schedule-german": 5,
            "schedule-english": 5,
            "schedule-french": 5,
            "schedule-dutch": 5,
            "schedule-mathematics": 5,
            "schedule-it": 5,
            "schedule-social_sciences": 5,
            "schedule-economic_sciences": 5,
            # Even if we send data for foreign diploma, it should be stripped from data sent to WS
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(sent, {
            'belgian_diploma': {
                'academic_graduation_year': 2020,
                "high_school_transcript": ["test"],
                "high_school_diploma": ["test"],
                'community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                'educational_other': '',
                'educational_type': EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
                'institute': '',
                'other_institute': 'Special school',
                'result': DiplomaResults.NOT_KNOWN_YET_RESULT.name,
                'schedule': {
                    'biology': 5,
                    'chemistry': 5,
                    'dutch': 5,
                    'economic_sciences': 5,
                    'english': 5,
                    'french': 5,
                    'german': 5,
                    'greek': 0,
                    'it': 5,
                    'latin': 5,
                    'mathematics': 5,
                    'modern_languages_other_hours': 0,
                    'modern_languages_other_label': '',
                    'other_hours': 0,
                    'other_label': '',
                    'physic': 5,
                    'social_sciences': 5
                }
            }
        })

    def test_form_belgian_bad_schedule(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.BELGIAN.name,
            "academic_graduation_year": 2020,
            "belgian_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
            "belgian_diploma-other_institute": "Special school",
            # Even if we send data for foreign diploma, it should be stripped from data sent to WS
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'schedule_form', None, _("A field of the schedule must at least be set."))
        self.mock_person_api.return_value.update_high_school_diploma.assert_not_called()

    def test_form_foreign(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "academic_graduation_year": 2020,
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-linguistic_regime": "AR",
            "foreign_diploma-country": "FR",
            "foreign_diploma-equivalence": Equivalence.PENDING.name,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'foreign_diploma_form', 'result', _("This field is required."))
        self.assertFormError(response, 'foreign_diploma_form', 'high_school_transcript_translation',
                             _("This field is required."))

        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "high_school_transcript_0": "test",
            "high_school_diploma_0": "test",
            "academic_graduation_year": 2020,
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-linguistic_regime": "AR",
            "foreign_diploma-country": "FR",
            "foreign_diploma-equivalence": Equivalence.PENDING.name,
            'foreign_diploma-high_school_transcript_translation_0': 'test',
            "foreign_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'foreign_diploma_form', 'high_school_diploma_translation',
                             _("This field is required."))

        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "academic_graduation_year": 2020,
            "high_school_transcript_0": "test",
            "high_school_diploma_0": "test",
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-linguistic_regime": "AR",
            "foreign_diploma-country": "FR",
            "foreign_diploma-equivalence": Equivalence.PENDING.name,
            'foreign_diploma-high_school_transcript_translation_0': 'test',
            'foreign_diploma-high_school_diploma_translation_0': 'test',
            "foreign_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            # Even if we send data for belgian diploma, it should be stripped from data sent to WS
            "belgian_diploma-other_institute": "Special school",
            # Even if we send data for schedule, it should be stripped from data sent to WS
            "schedule-greek": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(sent, {
            'foreign_diploma': {
                'academic_graduation_year': 2020,
                "high_school_transcript": ["test"],
                "high_school_diploma": ["test"],
                'result': DiplomaResults.NOT_KNOWN_YET_RESULT.name,
                'country': 'FR',
                'foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'linguistic_regime': 'AR',
                'other_linguistic_regime': '',
                'high_school_transcript_translation': ['test'],
                'high_school_diploma_translation': ['test'],
                'equivalence': Equivalence.PENDING.name,
            },
        })

    def test_form_will_get_diploma_this_year(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": get_current_year(),
                "result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            }
        }
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.THIS_YEAR.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "high_school_transcript_0": "test",
            "high_school_diploma_0": "test",
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-linguistic_regime": "EN",
            "foreign_diploma-country": "FR",
            "foreign_diploma-equivalence": "NO",
            "foreign_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            # Even if we send data for belgian diploma, it should be stripped from data sent to WS
            "belgian_diploma-other_institute": "Special school",
            # Even if we send data for schedule, it should be stripped from data sent to WS
            "schedule-greek": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(sent, {
            'foreign_diploma': {
                'academic_graduation_year': get_current_year(),
                "high_school_transcript": ["test"],
                "high_school_diploma": [],
                'result': DiplomaResults.NOT_KNOWN_YET_RESULT.name,
                'country': 'FR',
                'foreign_diploma_type': ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                'linguistic_regime': 'EN',
                'other_linguistic_regime': '',
                'high_school_transcript_translation': [],
                'high_school_diploma_translation': [],
                'equivalence': 'NO',
            },
        })

    def test_form_error_if_got_diploma_but_nothing_else(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('academic_graduation_year', response.context['main_form'].errors)
        self.assertIn('diploma_type', response.context['main_form'].errors)

    def test_form_error_if_hour_or_label_not_set(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.BELGIAN.name,
            "academic_graduation_year": 2020,
            "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
            "schedule-modern_languages_other_label": 'Chinese',
            "schedule-other_hours": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('modern_languages_other_hours', response.context['schedule_form'].errors)
        self.assertIn('other_label', response.context['schedule_form'].errors)

    def test_form_error_if_french_community_and_no_educational(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.BELGIAN.name,
            "academic_graduation_year": 2020,
            "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('educational_type', response.context['belgian_diploma_form'].errors)

    def test_form_error_linguistic_regime(self):
        response = self.client.post(self.form_url, {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "academic_graduation_year": 2020,
            "foreign_diploma-result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-country": "FR",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('linguistic_regime', response.context['foreign_diploma_form'].errors)

    def test_update_admission_in_context(self):
        url = resolve_url('admission:doctorate-update:education', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": 2020,
                "result": DiplomaResults.NOT_KNOWN_YET_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            }
        }

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_admission.assert_called()

    def test_detail_without_data(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {}

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, _("No secondary studies provided."))

    def test_detail_without_country_and_language(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "foreign_diploma": {
                "linguistic_regime": None,
                "country": None,
            }
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_belgian_diploma(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {
                "academic_graduation_year": 2020,
                "other_institute": "Special school",
                "schedule": {
                    "latin": 10,
                    "greek": 10,
                    "chemistry": 10,
                }
            },
            "foreign_diploma": {}
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Special school")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.assertIn('admission', response.context)

    def test_detail_foreign_diploma(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": 2019,
                "result": DiplomaResults.LT_65_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            }
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.assertIn('admission', response.context)
