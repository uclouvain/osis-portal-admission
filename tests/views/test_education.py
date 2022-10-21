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
import uuid
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_reference_sdk.model.high_school import HighSchool
from rest_framework import status
from rest_framework.status import HTTP_200_OK, HTTP_302_FOUND

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    DiplomaTypes,
    EducationalType,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
)
from admission.tests.utils import MockCountry, MockLanguage, MockHighSchool
from base.tests.factories.academic_year import get_current_year
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL="http://dummyurl.com/document/")
class EducationTestCase(TestCase):
    maxDiff = None
    REQUIRED_TEXT = _("This field is required.")

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.detail_url = resolve_url("admission:doctorate:education", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        cls.form_url = resolve_url("admission:create:education")
        cls.foreign_data = {
            "got_diploma": GotDiploma.YES.name,
            "diploma_type": DiplomaTypes.FOREIGN.name,
            "high_school_diploma_0": "test",
            "academic_graduation_year": 2020,
            "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "foreign_diploma-linguistic_regime": "EN",
            "foreign_diploma-country": "FR",
            "foreign_diploma-equivalence": Equivalence.PENDING.name,
            "foreign_diploma-high_school_transcript_0": "test",
            "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
            "foreign_diploma-final_equivalence_decision_ue_0": "test_ue",
            "foreign_diploma-final_equivalence_decision_not_ue_0": "test_not_ue",
        }

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        person_api_ret = self.mock_person_api.return_value
        default_return = {
            "belgian_diploma": None,
            "foreign_diploma": None,
        }
        person_api_ret.retrieve_high_school_diploma.return_value.to_dict.return_value = (
            person_api_ret.retrieve_high_school_diploma_admission.return_value.to_dict.return_value
        ) = default_return
        self.addCleanup(person_api_patcher.stop)

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        def get_countries(**kwargs):
            countries = [
                MockCountry(iso_code="FR", name="France", name_en="France", european_union=True),
                MockCountry(iso_code="BE", name="Belgique", name_en="Belgium", european_union=True),
                MockCountry(
                    iso_code="US",
                    name="États-Unis d'Amérique",
                    name_en="United States of America",
                    european_union=False,
                ),
            ]
            if kwargs.get("iso_code"):
                return Mock(results=[c for c in countries if c.iso_code == kwargs.get("iso_code")])
            return Mock(results=countries)

        self.mock_countries_api.return_value.countries_list.side_effect = get_countries
        self.addCleanup(countries_api_patcher.stop)

        patcher = patch("osis_document.api.utils.get_remote_token", return_value="foobar")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("osis_document.api.utils.get_remote_metadata", return_value={"name": "myfile"})
        patcher.start()
        self.addCleanup(patcher.stop)

        languages_api_patcher = patch("osis_reference_sdk.api.languages_api.LanguagesApi")
        self.mock_languages_api = languages_api_patcher.start()

        def get_languages(**kwargs):
            languages = [
                MockLanguage(code="FR", name="Français", name_en="French"),
                MockLanguage(code="EN", name="Anglais", name_en="English"),
                MockLanguage(code="AR", name="Arabe", name_en="Arabic"),
            ]
            if kwargs.get("code"):
                return Mock(results=[c for c in languages if c.code == kwargs.get("code")])
            return Mock(results=languages)

        self.mock_languages_api.return_value.languages_list.side_effect = get_languages
        self.addCleanup(languages_api_patcher.stop)

        high_schools_api_patcher = patch("osis_reference_sdk.api.high_schools_api.HighSchoolsApi")
        self.mock_high_schools_api = high_schools_api_patcher.start()

        self.first_high_school_uuid = str(uuid.uuid4())
        self.second_high_school_uuid = str(uuid.uuid4())
        self.third_high_school_uuid = str(uuid.uuid4())

        def get_high_schools(**kwargs):
            high_schools = [
                HighSchool(
                    uuid=self.first_high_school_uuid,
                    name="HighSchool 1",
                    city="Louvain-La-Neuve",
                    zipcode="1348",
                    street="Place de l'Université",
                    street_number="1",
                ),
                HighSchool(
                    uuid=self.second_high_school_uuid,
                    name="HighSchool 2",
                    city="Louvain-La-Neuve",
                    zipcode="1348",
                    street="Place de l'Université",
                    street_number="1",
                ),
                HighSchool(
                    uuid=self.third_high_school_uuid,
                    name="HighSchool 3",
                    city="Bruxelles",
                    zipcode="1000",
                    street="Boulevard du Triomphe",
                    street_number="1",
                ),
            ]
            if kwargs.get("uuid"):
                return next((school for school in high_schools if school.uuid == kwargs["uuid"]), None)
            return Mock(results=high_schools)

        self.mock_high_schools_api.return_value.high_schools_list.side_effect = get_high_schools
        self.mock_high_schools_api.return_value.high_school_read.side_effect = get_high_schools
        self.addCleanup(high_schools_api_patcher.stop)

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
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "high_school_diploma_0": "test",
                "enrolment_certificate_0": "test",
                "academic_graduation_year": 2020,
                "belgian_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                "belgian_diploma-institute": self.first_high_school_uuid,
                "belgian_diploma-other_institute": False,
                "belgian_diploma-other_institute_name": "Special school",
                # Even if we send data for schedule, it should be stripped from data sent to WS
                "schedule-greek": 5,
                # Even if we send data for foreign diploma, it should be stripped from data sent to WS
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "belgian_diploma": {
                    "academic_graduation_year": 2020,
                    "community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                    "high_school_diploma": ["test"],
                    "enrolment_certificate": [],
                    "result": DiplomaResults.GT_75_RESULT.name,
                    # Clean other institute
                    "institute": self.first_high_school_uuid,
                    "other_institute_name": "",
                    "other_institute_address": "",
                    # Clean education type
                    "educational_type": "",
                    "educational_other": "",
                },
                "specific_question_answers": {},
            },
        )

    def test_form_belgian_schedule(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "academic_graduation_year": 2020,
                "high_school_diploma_0": "test",
                "belgian_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                "schedule-latin": 5,
                "schedule-chemistry": 5,
                "schedule-physic": 5,
                "schedule-biology": 5,
                "schedule-german": 5,
                "schedule-english": 5,
                "schedule-french": 5,
                "schedule-dutch": 5,
                "schedule-mathematics": 5,
                "schedule-spanish": 5,
                "schedule-it": 5,
                "schedule-social_sciences": 5,
                "schedule-economic_sciences": 5,
                # Even if we send data for foreign diploma, it should be stripped from data sent to WS
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "belgian_diploma": {
                    "academic_graduation_year": 2020,
                    "enrolment_certificate": [],
                    "high_school_diploma": ["test"],
                    "community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                    "educational_other": "",
                    "educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
                    "institute": "",
                    "other_institute_name": "Special school",
                    "other_institute_address": "Louvain-La-Neuve",
                    "result": DiplomaResults.GT_75_RESULT.name,
                    "schedule": {
                        "biology": 5,
                        "chemistry": 5,
                        "dutch": 5,
                        "economic_sciences": 5,
                        "english": 5,
                        "french": 5,
                        "german": 5,
                        "greek": 0,
                        "it": 5,
                        "latin": 5,
                        "mathematics": 5,
                        "spanish": 5,
                        "modern_languages_other_hours": 0,
                        "modern_languages_other_label": "",
                        "other_hours": 0,
                        "other_label": "",
                        "physic": 5,
                        "social_sciences": 5,
                    },
                },
                "specific_question_answers": {},
            },
        )

    def test_form_belgian_bad_schedule(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "academic_graduation_year": 2020,
                "belgian_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                # Even if we send data for foreign diploma, it should be stripped from data sent to WS
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "schedule_form", None, _("A field of the schedule must at least be set."))
        self.mock_person_api.return_value.update_high_school_diploma.assert_not_called()

    def test_form_foreign_error_if_no_translations_when_needed_for_this_year_in_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "high_school_diploma_0": "test",
                "enrolment_certificate_0": "test",
                "high_school_transcript_0": "test",
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "BE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in [
            "high_school_transcript_translation",
            "high_school_diploma_translation",
            "enrolment_certificate_translation",
        ]:
            self.assertFormError(response, "foreign_diploma_form", field, self.REQUIRED_TEXT)

    def test_form_foreign_error_if_no_translations_when_needed_for_this_year_in_not_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "high_school_diploma_0": "test",
                "enrolment_certificate_0": "test",
                "high_school_transcript_0": "test",
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "BE",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in [
            "high_school_transcript_translation",
            "high_school_diploma_translation",
        ]:
            self.assertFormError(response, "foreign_diploma_form", field, self.REQUIRED_TEXT)

    def test_form_foreign_error_if_no_translations_when_needed_for_past_year(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "high_school_diploma_0": "test",
                "enrolment_certificate_0": "test",
                "high_school_transcript_0": "test",
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "BE",
                "academic_graduation_year": 2020,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field in [
            "high_school_transcript_translation",
            "high_school_diploma_translation",
        ]:
            self.assertFormError(response, "foreign_diploma_form", field, self.REQUIRED_TEXT)

    def test_form_foreign_error_if_got_diploma_this_year_without_attachments_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "academic_graduation_year": 2020,
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "FR",
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFormError(
            response,
            "main_form",
            "high_school_diploma",
            _("Please specify either your high school diploma or your enrolment certificate"),
        )

    def test_form_foreign_error_if_got_diploma_this_year_without_attachments_for_not_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "academic_graduation_year": 2020,
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "US",
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFormError(response, "main_form", "high_school_diploma", self.REQUIRED_TEXT)

    def test_form_foreign_error_if_no_equivalence_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "foreign_diploma_form", "equivalence", self.REQUIRED_TEXT)

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.NO.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"][
            "foreign_diploma"
        ]
        self.assertEqual(sent.get("equivalence"), Equivalence.NO.name)
        self.assertEqual(sent.get("final_equivalence_decision"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_form_foreign_pending_equivalence_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
                "foreign_diploma-equivalence_decision_proof_0": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "foreign_diploma_form", "equivalence_decision_proof", self.REQUIRED_TEXT)

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
                "foreign_diploma-equivalence_decision_proof_0": "test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"][
            "foreign_diploma"
        ]
        self.assertEqual(sent.get("equivalence"), Equivalence.PENDING.name)
        self.assertEqual(sent.get("final_equivalence_decision"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), ["test"])

    def test_form_foreign_existing_equivalence_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.YES.name,
                "foreign_diploma-final_equivalence_decision_ue_0": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "foreign_diploma_form", "final_equivalence_decision_ue", self.REQUIRED_TEXT)

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.YES.name,
                "foreign_diploma-final_equivalence_decision_ue_0": "test_ue",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"][
            "foreign_diploma"
        ]
        self.assertEqual(sent.get("equivalence"), Equivalence.YES.name)
        self.assertEqual(sent.get("final_equivalence_decision"), ["test_ue"])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_form_foreign_existing_equivalence_for_not_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
                "foreign_diploma-final_equivalence_decision_not_ue_0": "",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "foreign_diploma_form", "final_equivalence_decision_not_ue", self.REQUIRED_TEXT)

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
                "foreign_diploma-final_equivalence_decision_not_ue_0": "test_not_ue",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"][
            "foreign_diploma"
        ]
        self.assertEqual(sent.get("equivalence"), '')
        self.assertEqual(sent.get("final_equivalence_decision"), ["test_not_ue"])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_form_foreign(self):
        # Complete international baccalaureate
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "academic_graduation_year": 2020,
                "foreign_diploma-high_school_transcript_0": "test",
                "high_school_diploma_0": "test",
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.INTERNATIONAL_BACCALAUREATE.name,
                "foreign_diploma-other_linguistic_regime": "FR",
                "foreign_diploma-country": "FR",
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma-high_school_transcript_translation_0": "test",
                "foreign_diploma-high_school_diploma_translation_0": "test",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "foreign_diploma": {
                    "academic_graduation_year": 2020,
                    "high_school_transcript": ["test"],
                    "high_school_diploma": ["test"],
                    "result": DiplomaResults.GT_75_RESULT.name,
                    "country": "FR",
                    "foreign_diploma_type": ForeignDiplomaTypes.INTERNATIONAL_BACCALAUREATE.name,
                    "linguistic_regime": "",
                    "other_linguistic_regime": "FR",
                    "high_school_transcript_translation": ["test"],
                    "high_school_diploma_translation": ["test"],
                    "equivalence": "",
                    "enrolment_certificate": [],
                    "enrolment_certificate_translation": [],
                    "equivalence_decision_proof": [],
                    "final_equivalence_decision": [],
                },
                "specific_question_answers": {},
            },
        )

        # Complete national bachelor
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "academic_graduation_year": 2020,
                "foreign_diploma-high_school_transcript_0": "test",
                "high_school_diploma_0": "test",
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-linguistic_regime": "AR",
                "foreign_diploma-country": "FR",
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
                "foreign_diploma-equivalence_decision_proof_0": "test",
                "foreign_diploma-high_school_transcript_translation_0": "test",
                "foreign_diploma-high_school_diploma_translation_0": "test",
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
                # Even if we send data for belgian diploma, it should be stripped from data sent to WS
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                # Even if we send data for schedule, it should be stripped from data sent to WS
                "schedule-greek": 5,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "foreign_diploma": {
                    "academic_graduation_year": 2020,
                    "high_school_transcript": ["test"],
                    "high_school_diploma": ["test"],
                    "result": DiplomaResults.GT_75_RESULT.name,
                    "country": "FR",
                    "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                    "linguistic_regime": "AR",
                    "other_linguistic_regime": "",
                    "high_school_transcript_translation": ["test"],
                    "high_school_diploma_translation": ["test"],
                    "equivalence": Equivalence.PENDING.name,
                    "enrolment_certificate": [],
                    "enrolment_certificate_translation": [],
                    "equivalence_decision_proof": ["test"],
                    "final_equivalence_decision": [],
                },
                "specific_question_answers": {},
            },
        )

    def test_form_no_high_school_diploma(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {},
            "high_school_diploma_alternative": {
                "first_cycle_admission_exam": ["test"],
            },
        }
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.NO.name,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, "main_form", "first_cycle_admission_exam", _("This field is required."))

        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.NO.name,
                "first_cycle_admission_exam_0": "test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "high_school_diploma_alternative": {
                    "first_cycle_admission_exam": ["test"],
                },
            },
        )

    def test_form_will_get_foreign_diploma_this_year(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": get_current_year(),
                "result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            },
        }
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "foreign_diploma-high_school_transcript_0": "test",
                "high_school_diploma_0": "test",
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-linguistic_regime": "EN",
                "foreign_diploma-country": "FR",
                "foreign_diploma-equivalence": "NO",
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
                # Even if we send data for belgian diploma, it should be stripped from data sent to WS
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                # Even if we send data for schedule, it should be stripped from data sent to WS
                "schedule-greek": 5,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma.call_args[1]["high_school_diploma"]
        self.assertEqual(
            sent,
            {
                "foreign_diploma": {
                    "academic_graduation_year": get_current_year(),
                    "high_school_transcript": ["test"],
                    "high_school_diploma": ["test"],
                    "enrolment_certificate": [],
                    "enrolment_certificate_translation": [],
                    "equivalence_decision_proof": [],
                    "result": DiplomaResults.GT_75_RESULT.name,
                    "country": "FR",
                    "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                    "linguistic_regime": "EN",
                    "other_linguistic_regime": "",
                    "high_school_transcript_translation": [],
                    "high_school_diploma_translation": [],
                    "equivalence": "NO",
                    "final_equivalence_decision": [],
                },
                "specific_question_answers": {},
            },
        )
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "foreign_diploma-high_school_transcript_0": "test",
                "high_school_diploma_0": "test",
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.INTERNATIONAL_BACCALAUREATE.name,
                "foreign_diploma-linguistic_regime": "EN",
                "foreign_diploma-country": "US",
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_form_will_get_belgian_diploma_this_year(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma.return_value.to_dict.return_value = {
            "belgian_diploma": {
                "academic_graduation_year": get_current_year(),
            },
            "foreign_diploma": {},
        }
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "belgian_diploma-other_institute": True,
                "schedule-greek": 5,
            },
        )
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(
            response,
            "main_form",
            "high_school_diploma",
            _("Please specify either your high school diploma or your enrolment certificate"),
        )
        self.assertFormError(
            response,
            "belgian_diploma_form",
            "other_institute_name",
            FIELD_REQUIRED_MESSAGE,
        )
        self.assertFormError(
            response,
            "belgian_diploma_form",
            "other_institute_address",
            FIELD_REQUIRED_MESSAGE,
        )
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "enrolment_certificate_0": "test",
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                "schedule-greek": 5,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                "belgian_diploma-result": DiplomaResults.GT_75_RESULT.name,
            },
        )
        self.assertEqual(response.status_code, HTTP_302_FOUND)

    def test_form_error_if_got_diploma_but_nothing_else(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("academic_graduation_year", response.context["main_form"].errors)
        self.assertIn("diploma_type", response.context["main_form"].errors)
        self.assertIn("high_school_diploma", response.context["main_form"].errors)

    def test_belgian_form_error_if_hour_or_label_not_set(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "academic_graduation_year": 2020,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
                "schedule-modern_languages_other_label": "Chinese",
                "schedule-other_hours": 5,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("modern_languages_other_hours", response.context["schedule_form"].errors)
        self.assertIn("other_label", response.context["schedule_form"].errors)

    def test_belgian_form_error_if_french_community_and_no_educational(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "academic_graduation_year": 2020,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("educational_type", response.context["belgian_diploma_form"].errors)

    def test_belgian_form_error_if_no_institute(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "academic_graduation_year": 2020,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("institute", response.context["belgian_diploma_form"].errors)
        self.assertIn("other_institute", response.context["belgian_diploma_form"].errors)

    def test_belgian_form_error_linguistic_regime(self):
        response = self.client.post(
            self.form_url,
            {
                "got_diploma": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "academic_graduation_year": 2020,
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-country": "FR",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("linguistic_regime", response.context["foreign_diploma_form"].errors)

    def test_update_admission_in_context(self):
        url = resolve_url("admission:doctorate:update:education", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": 2020,
                "result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            },
        }

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn("admission", response.context)

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
                "other_institute_name": "Special school",
                "other_institute_address": "Louvain-La-Neuve",
                "schedule": {
                    "latin": 10,
                    "greek": 10,
                    "chemistry": 10,
                },
            },
            "foreign_diploma": {},
            "high_school_diploma_alternative": {},
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Special school (Louvain-La-Neuve)")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.assertIn("admission", response.context)

        # With specified institute
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {
                "academic_graduation_year": 2020,
                "institute": self.first_high_school_uuid,
            },
            "foreign_diploma": {},
            "high_school_diploma_alternative": {},
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "HighSchool 1 (Louvain-La-Neuve)")

    def test_detail_foreign_diploma(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": 2019,
                "result": DiplomaResults.LT_65_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "country": "FR",
            },
            "high_school_diploma_alternative": {},
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.assertIn("admission", response.context)

    def test_detail_alternative_diploma(self):
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value.to_dict.return_value = {
            "belgian_diploma": {},
            "foreign_diploma": {},
            "high_school_diploma_alternative": {
                "first_cycle_admission_exam": ["test"],
            },
        }

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(
            response,
            _("Certificate of successful completion of the admission test for the first cycle of higher education"),
        )
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.assertIn("admission", response.context)
