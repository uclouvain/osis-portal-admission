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
from unittest.mock import ANY, Mock, patch

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_reference_sdk.model.high_school import HighSchool
from rest_framework import status
from rest_framework.status import HTTP_302_FOUND

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums import ChoixStatutPropositionGenerale, TrainingType
from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    DiplomaTypes,
    EducationalType,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
)
from admission.contrib.forms import PDF_MIME_TYPE
from admission.tests import get_paginated_years
from admission.tests.utils import MockCountry, MockLanguage
from base.tests.factories.academic_year import get_current_year
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL="http://dummyurl.com/document/")
class BaseEducationTestCase(TestCase):
    REQUIRED_TEXT = _("This field is required.")

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.proposition_uuid = uuid.uuid4()
        cls.proposition_uuid_str = str(cls.proposition_uuid)
        cls.first_question_uuid = str(uuid.uuid4())

        cls.proposition = Mock(
            uuid=cls.proposition_uuid,
            formation=Mock(
                annee=2020,
                intitule='Formation',
                campus='Louvain-La-Neuve',
                sigle='TR1',
                type=TrainingType.MASTER_M1.name,
                code_domaine='10A',
            ),
            matricule_candidat=cls.person.global_id,
            prenom_candidat=cls.person.first_name,
            nom_candidat=cls.person.last_name,
            statut=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
            links={},
            erreurs={},
            bourse_double_diplome=None,
            bourse_internationale=None,
            bourse_erasmus_mundus=None,
            reponses_questions_specifiques={
                cls.first_question_uuid: 'My answer',
            },
        )

        cls.detail_url = resolve_url("admission:general-education:education", pk=cls.proposition_uuid)
        cls.form_url = resolve_url("admission:general-education:update:education", pk=cls.proposition_uuid)
        cls.create_url = resolve_url("admission:create:education")

        cls.foreign_data = {
            "graduated_from_high_school": GotDiploma.YES.name,
            "graduated_from_high_school_year": 2020,
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

        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.return_value = self.proposition
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        person_api_ret = self.mock_person_api.return_value
        self.mock_retrieve_high_school_diploma_for_general = {
            "graduated_from_high_school": "",
            "graduated_from_high_school_year": None,
            "belgian_diploma": None,
            "foreign_diploma": None,
            "high_school_diploma_alternative": None,
            "is_vae_potential": False,
            "is_valuated": False,
        }
        person_api_ret.retrieve_high_school_diploma_general_education_admission.return_value.to_dict.return_value = (
            self.mock_retrieve_high_school_diploma_for_general
        )

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
        patcher = patch(
            "osis_document.api.utils.get_remote_metadata",
            return_value={"name": "myfile", 'mimetype': PDF_MIME_TYPE},
        )
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
        year = datetime.today().year
        self.mock_academic_year_api.return_value.get_academic_years.return_value = get_paginated_years(
            year - 2,
            year + 2,
        )
        self.addCleanup(academic_year_api_patcher.stop)


@freezegun.freeze_time('2022-01-01')
class EducationTestCase(BaseEducationTestCase):
    def test_detail_without_specified_graduation(self):
        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js", count=1)

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )

        # Check response context
        self.assertEqual(response.context['admission'], self.proposition)
        self.assertEqual(response.context['belgian_diploma'], None)
        self.assertEqual(response.context['foreign_diploma'], None)
        self.assertEqual(response.context['high_school_diploma_alternative'], None)
        self.assertEqual(response.context['graduated_from_high_school_year'], None)
        self.assertEqual(response.context['graduated_from_high_school'], "")
        self.assertEqual(response.context['is_vae_potential'], False)

        # Check template
        self.assertContains(response, 'Non renseigné(e)')

    def test_detail_with_graduation_from_high_school(self):
        self.mock_retrieve_high_school_diploma_for_general['graduated_from_high_school'] = GotDiploma.YES.name
        self.mock_retrieve_high_school_diploma_for_general['graduated_from_high_school_year'] = 2020

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(response.context['graduated_from_high_school_year'], 2020)
        self.assertEqual(response.context['graduated_from_high_school'], GotDiploma.YES.name)

        # Check template
        self.assertContains(response, 'Oui, en 2020-21.')

    def test_detail_with_graduation_from_high_school_this_year(self):
        self.mock_retrieve_high_school_diploma_for_general['graduated_from_high_school'] = GotDiploma.THIS_YEAR.name
        self.mock_retrieve_high_school_diploma_for_general['graduated_from_high_school_year'] = 2020

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(response.context['graduated_from_high_school_year'], 2020)
        self.assertEqual(response.context['graduated_from_high_school'], GotDiploma.THIS_YEAR.name)

        # Check template
        self.assertContains(response, "Vous avez indiqué que vous alliez l\'obtenir en 2020-21.", html=True)

    def test_detail_without_graduation_from_high_school_this_year(self):
        self.mock_retrieve_high_school_diploma_for_general['graduated_from_high_school'] = GotDiploma.NO.name

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(response.context['graduated_from_high_school'], GotDiploma.NO.name)

        # Check template
        self.assertContains(response, 'Non.')

    def test_detail_without_country_and_language(self):
        self.mock_retrieve_high_school_diploma_for_general = {
            "foreign_diploma": {
                "linguistic_regime": None,
                "other_linguistic_regime": "",
                "country": None,
            }
        }

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self):
        response = self.client.get(self.create_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js", count=1)

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        # Check template content
        self.assertContains(
            response,
            _("You must choose your course before entering your previous experience."),
        )

    def test_form_initialization(self):
        response = self.client.get(self.form_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "dependsOn.min.js", count=1)
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )

        # Check response context
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].fields['graduated_from_high_school'].required)
        self.assertFalse(response.context['form'].fields['graduated_from_high_school_year'].required)
        self.assertIn('specific_question_answers', response.context['form'].fields)
        for field in ['graduated_from_high_school', 'graduated_from_high_school_year']:
            self.assertFalse(response.context['form'].fields[field].disabled)
        self.assertEqual(len(response.context['form'].visible_fields()), 2)

    def test_form_initialization_with_valuated_experience(self):
        self.mock_retrieve_high_school_diploma_for_general['is_valuated'] = True
        response = self.client.get(self.form_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )

        # Check response context
        self.assertIn('form', response.context)
        for field in ['graduated_from_high_school', 'graduated_from_high_school_year']:
            self.assertTrue(response.context['form'].fields[field].disabled)

    def test_form_submission_if_empty(self):
        response = self.client.post(self.form_url, {})

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_not_called()

        # Check response context
        form = response.context['form']
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('graduated_from_high_school', []))

    def test_form_submission_if_got_diploma_and_no_year(self):
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
            },
        )

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_not_called()

        # Check response context
        form = response.context['form']
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('graduated_from_high_school_year', []))

    def test_form_submission_if_got_diploma_and_year(self):
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': 2020,
            },
        )

        # Check response status
        self.assertRedirects(response, expected_url=self.detail_url)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            high_school_diploma={
                'graduated_from_high_school': GotDiploma.YES.name,
                'graduated_from_high_school_year': 2020,
                'specific_question_answers': self.proposition.reponses_questions_specifiques,
            },
            **self.default_kwargs,
        )

    @freezegun.freeze_time(datetime(2020, 12, 1))
    def test_form_submission_if_got_diploma_this_year_and_other_year(self):
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'graduated_from_high_school_year': 2012,
            },
        )

        # Check response status
        self.assertRedirects(response, expected_url=self.detail_url)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            high_school_diploma={
                'graduated_from_high_school': GotDiploma.THIS_YEAR.name,
                'graduated_from_high_school_year': 2020,
                'specific_question_answers': self.proposition.reponses_questions_specifiques,
            },
            **self.default_kwargs,
        )

    def test_form_submission_if_no_diploma(self):
        response = self.client.post(
            self.form_url,
            {
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': 2020,
            },
        )

        # Check response status
        self.assertRedirects(response, expected_url=self.detail_url)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            high_school_diploma={
                'graduated_from_high_school': GotDiploma.NO.name,
                'graduated_from_high_school_year': None,
                'specific_question_answers': self.proposition.reponses_questions_specifiques,
            },
            **self.default_kwargs,
        )


@freezegun.freeze_time('2022-01-01')
class BachelorFormEducationTestCase(BaseEducationTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.proposition.formation.type = TrainingType.BACHELOR.name

    def test_detail_belgian_diploma(self):
        self.mock_retrieve_high_school_diploma_for_general['belgian_diploma'] = {
            "academic_graduation_year": 2020,
            "other_institute_name": "Special school",
            "other_institute_address": "Louvain-La-Neuve",
        }

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(
            response.context['belgian_diploma'],
            {
                "academic_graduation_year": 2020,
                "institute_name": "Special school",
                "institute_address": "Louvain-La-Neuve",
            },
        )

        # Check template
        self.assertContains(response, "Special school (Louvain-La-Neuve)")

        # With existing institute
        self.mock_retrieve_high_school_diploma_for_general['belgian_diploma']['institute'] = self.first_high_school_uuid

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        institute_address = "Place de l'Université 1, 1348 Louvain-La-Neuve"
        self.assertContains(response, "Diplôme belge")
        self.assertEqual(response.context['belgian_diploma']['institute_name'], 'HighSchool 1')
        self.assertEqual(response.context['belgian_diploma']['institute_address'], institute_address)

        # Check template
        self.assertContains(response, f"HighSchool 1 ({institute_address})")

    def test_detail_foreign_diploma(self):
        self.mock_retrieve_high_school_diploma_for_general['foreign_diploma'] = {
            "academic_graduation_year": 2019,
            "result": DiplomaResults.LT_65_RESULT.name,
            "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "linguistic_regime": "EN",
            "other_linguistic_regime": "",
            "country": "FR",
        }

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(
            response.context['foreign_diploma'],
            {
                "academic_graduation_year": 2019,
                "result": DiplomaResults.LT_65_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "Anglais",
                "other_linguistic_regime": "",
                "country": {'european_union': True, 'name': 'France'},
            },
        )

        # Check template
        self.assertContains(response, "Diplôme étranger")
        self.assertContains(response, "France")
        self.assertContains(response, "Anglais")

        self.mock_retrieve_high_school_diploma_for_general['foreign_diploma'] = {
            "academic_graduation_year": 2019,
            "result": DiplomaResults.LT_65_RESULT.name,
            "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            "linguistic_regime": None,
            "other_linguistic_regime": "Français",
            "country": "FR",
        }

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check template
        self.assertContains(response, "Diplôme étranger")
        self.assertContains(response, "Français")

    def test_detail_alternative_diploma(self):
        self.mock_retrieve_high_school_diploma_for_general['high_school_diploma_alternative'] = {
            "first_cycle_admission_exam": ["test"],
        }

        response = self.client.get(self.detail_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response context
        self.assertEqual(
            response.context['high_school_diploma_alternative'],
            {
                "first_cycle_admission_exam": ["test"],
            },
        )

        self.assertContains(
            response,
            _("Certificate of passing the bachelor's course entrance exam"),
        )
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called()
        self.assertIn("admission", response.context)

    def test_bachelor_form_initialization(self):
        response = self.client.get(self.form_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )

        # Check response context
        self.assertIn('main_form', response.context)
        self.assertIn('belgian_diploma_form', response.context)
        self.assertIn('foreign_diploma_form', response.context)

    def test_form_initialization_with_valuated_experience(self):
        self.mock_retrieve_high_school_diploma_for_general['is_valuated'] = True
        response = self.client.get(self.form_url)

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.retrieve_high_school_diploma_general_education_admission.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )
        self.mock_proposition_api.return_value.retrieve_general_education_proposition.assert_called_with(
            uuid=self.proposition_uuid_str,
            **self.default_kwargs,
        )

        # Check response context
        self.assertIn('form', response.context)
        for field in ['graduated_from_high_school', 'graduated_from_high_school_year']:
            self.assertTrue(response.context['form'].fields[field].disabled)

    def test_bachelor_form_empty(self):
        self.proposition.formation.type = TrainingType.BACHELOR.name

        response = self.client.post(self.form_url, {})

        # Check response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check api calls
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_not_called()

        # Check response context
        form = response.context['form']
        self.assertIn(FIELD_REQUIRED_MESSAGE, form.errors.get('graduated_from_high_school', []))

    def test_bachelor_form_belgian(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "high_school_diploma_0": "test",
                "enrolment_certificate_0": "test",
                "graduated_from_high_school_year": 2020,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                "belgian_diploma-institute": self.first_high_school_uuid,
                "belgian_diploma-other_institute": False,
                "belgian_diploma-other_institute_name": "Special school",
                # Even if we send data for foreign diploma, it should be stripped from data sent to WS
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "graduated_from_high_school_year": 2020,
                "belgian_diploma": {
                    "academic_graduation_year": 2020,
                    "community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                    "high_school_diploma": ["test"],
                    "enrolment_certificate": [],
                    # Clean other institute
                    "institute": self.first_high_school_uuid,
                    "other_institute_name": "",
                    "other_institute_address": "",
                    # Clean education type
                    "educational_type": "",
                    "educational_other": "",
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )

    def test_bachelor_form_foreign_error_if_no_equivalence_for_ue_country(self):
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
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.NO.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), [])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_bachelor_form_foreign_pending_equivalence_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
                "foreign_diploma-equivalence_decision_proof_0": "test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.PENDING.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), [])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), ["test"])

    def test_bachelor_form_foreign_existing_equivalence_for_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-equivalence": Equivalence.YES.name,
                "foreign_diploma-final_equivalence_decision_ue_0": "test_ue",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.YES.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), ["test_ue"])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_bachelor_form_foreign_error_if_no_equivalence_for_ue_country_equivalence(self):
        self.proposition.formation.code_domaine = '11A'

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
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
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.NO.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), [])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_bachelor_form_foreign_pending_equivalence_for_ue_country_equivalence(self):
        self.proposition.formation.code_domaine = '11A'

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
                "foreign_diploma-equivalence": Equivalence.PENDING.name,
                "foreign_diploma-equivalence_decision_proof_0": "test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.PENDING.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), [])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), ["test"])

    def test_bachelor_form_foreign_existing_equivalence_for_ue_country_equivalence(self):
        self.proposition.formation.code_domaine = '11A'

        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
                "foreign_diploma-equivalence": Equivalence.YES.name,
                "foreign_diploma-final_equivalence_decision_ue_0": "test_ue",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), Equivalence.YES.name)
        self.assertEqual(sent.get("final_equivalence_decision_ue"), ["test_ue"])
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_bachelor_form_foreign_existing_equivalence_for_not_ue_country(self):
        response = self.client.post(
            self.form_url,
            {
                **self.foreign_data,
                "foreign_diploma-country": "US",
                "foreign_diploma-final_equivalence_decision_not_ue_0": "test_not_ue",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]["foreign_diploma"]
        self.assertEqual(sent.get("equivalence"), '')
        self.assertEqual(sent.get("final_equivalence_decision_not_ue"), ["test_not_ue"])
        self.assertEqual(sent.get("final_equivalence_decision_ue"), [])
        self.assertEqual(sent.get("equivalence_decision_proof"), [])

    def test_bachelor_form_foreign(self):
        # Complete international baccalaureate
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "graduated_from_high_school_year": 2020,
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

        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "graduated_from_high_school_year": 2020,
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
                    "final_equivalence_decision_ue": [],
                    "final_equivalence_decision_not_ue": [],
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )

        # Complete national bachelor
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "graduated_from_high_school_year": 2020,
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
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "graduated_from_high_school_year": 2020,
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
                    "final_equivalence_decision_ue": [],
                    "final_equivalence_decision_not_ue": [],
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )

    def test_bachelor_form_no_high_school_diploma(self):
        self.mock_retrieve_high_school_diploma_for_general = {
            "belgian_diploma": {},
            "foreign_diploma": {},
            "high_school_diploma_alternative": {
                "first_cycle_admission_exam": ["test"],
            },
        }

        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.NO.name,
                "first_cycle_admission_exam_0": "test",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.NO.name,
                "graduated_from_high_school_year": None,
                "high_school_diploma_alternative": {
                    "first_cycle_admission_exam": ["test"],
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )

    @freezegun.freeze_time(datetime(2020, 12, 1))
    def test_bachelor_form_will_get_foreign_diploma_this_year(self):
        self.mock_retrieve_high_school_diploma_for_general = {
            "belgian_diploma": {},
            "foreign_diploma": {
                "academic_graduation_year": get_current_year(),
                "result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "linguistic_regime": "EN",
                "other_linguistic_regime": "",
                "country": "FR",
            },
        }
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
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
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
                "graduated_from_high_school_year": 2020,
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
                    "final_equivalence_decision_ue": [],
                    "final_equivalence_decision_not_ue": [],
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
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

    @freezegun.freeze_time(datetime(2020, 12, 1))
    def test_bachelor_form_will_get_belgian_diploma_this_year(self):
        self.mock_retrieve_high_school_diploma_for_general = {
            "belgian_diploma": {
                "academic_graduation_year": get_current_year(),
            },
            "foreign_diploma": {},
        }
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "enrolment_certificate_0": "test",
                "high_school_diploma_0": "test",
                "belgian_diploma-other_institute": True,
                "belgian_diploma-other_institute_name": "Special school",
                "belgian_diploma-other_institute_address": "Louvain-La-Neuve",
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
            },
        )
        self.assertEqual(response.status_code, HTTP_302_FOUND)
        self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.assert_called()
        sent = self.mock_person_api.return_value.update_high_school_diploma_general_education_admission.call_args[1][
            "high_school_diploma"
        ]
        self.assertEqual(
            sent,
            {
                "graduated_from_high_school": GotDiploma.THIS_YEAR.name,
                "graduated_from_high_school_year": 2020,
                "belgian_diploma": {
                    "academic_graduation_year": 2020,
                    "community": BelgianCommunitiesOfEducation.FLEMISH_SPEAKING.name,
                    "high_school_diploma": [],
                    "enrolment_certificate": ["test"],
                    # Clean other institute
                    "institute": '',
                    "other_institute_name": "Special school",
                    "other_institute_address": "Louvain-La-Neuve",
                    # Clean education type
                    "educational_type": "",
                    "educational_other": "",
                },
                "specific_question_answers": self.proposition.reponses_questions_specifiques,
            },
        )

    def test_bachelor_form_error_if_got_diploma_but_nothing_else(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("graduated_from_high_school_year", response.context["main_form"].errors)
        self.assertIn("diploma_type", response.context["main_form"].errors)

    def test_bachelor_belgian_form_error_if_hour_or_label_not_set(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "graduated_from_high_school_year": 2020,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
                "belgian_diploma-educational_type": EducationalType.TEACHING_OF_GENERAL_EDUCATION.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bachelor_belgian_form_error_if_french_community_and_no_educational(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "graduated_from_high_school_year": 2020,
                "belgian_diploma-community": BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("educational_type", response.context["belgian_diploma_form"].errors)

    def test_bachelor_belgian_form_error_if_no_institute(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.BELGIAN.name,
                "graduated_from_high_school_year": 2020,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("institute", response.context["belgian_diploma_form"].errors)
        self.assertIn("other_institute", response.context["belgian_diploma_form"].errors)

    def test_bachelor_belgian_form_error_linguistic_regime(self):
        response = self.client.post(
            self.form_url,
            {
                "graduated_from_high_school": GotDiploma.YES.name,
                "diploma_type": DiplomaTypes.FOREIGN.name,
                "graduated_from_high_school_year": 2020,
                "foreign_diploma-result": DiplomaResults.GT_75_RESULT.name,
                "foreign_diploma-foreign_diploma_type": ForeignDiplomaTypes.NATIONAL_BACHELOR.name,
                "foreign_diploma-country": "FR",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("linguistic_regime", response.context["foreign_diploma_form"].errors)
