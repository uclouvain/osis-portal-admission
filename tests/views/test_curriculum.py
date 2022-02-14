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
from unittest.mock import patch, Mock, ANY

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_admission_sdk import ApiException
from rest_framework.status import HTTP_200_OK

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.curriculum import ExperienceType, ActivityType
from admission.contrib.views.form_tabs.curriculum import CurriculumForm
from admission.tests.utils import MockCountry, MockLanguage
from base.tests.factories.person import PersonFactory


class ExtendedTestCase(TestCase):
    def assertSubFormError(self, response, sub_form_name, field, error):
        for i, context in enumerate(response.context):
            if 'forms' not in context:
                continue
            if sub_form_name not in context['forms']:
                break
            form = context['forms'][sub_form_name]
            if error in form.errors.get(field, []):
                return
        self.fail(
            "The field '%s' on form '%s' doesn't exist or doesn't contain any error." %
            (field, sub_form_name)
        )


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl')
class CurriculumTestCase(ExtendedTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

        cls.api_default_params = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

    def setUp(self):
        self.url = resolve_url("admission:doctorate-update:cotutelle", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        # Mock proposition api
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            code_secteur_formation="SSH",
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            links={},
        )
        self.addCleanup(propositions_api_patcher.stop)

        # Mock person api
        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_proposition_api = person_api_patcher.start()
        self.mock_proposition_api.return_value.retrieve_proposition.return_value = Mock(
            code_secteur_formation="SSH",
            documents_projet=[],
            graphe_gantt=[],
            proposition_programme_doctoral=[],
            projet_formation_complementaire=[],
            lettres_recommandation=[],
            links={},
        )
        self.addCleanup(person_api_patcher.stop)

        api_person_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = api_person_patcher.start()

        self.first_uuid = uuid.uuid4()
        self.second_uuid = uuid.uuid4()
        self.other_uuid = uuid.uuid4()

        mock_first_experience = Mock(
            uuid=self.first_uuid,
            curriculum_year=Mock(
                academic_year=2020,
                id=1,
            ),
            country=BE_ISO_CODE,
            type=ExperienceType.OTHER_ACTIVITY.name,
            institute_name='UCL',
            institute_city='Louvain-La-Neuve',
            activity_type=ActivityType.WORK.name,
            activity_position='Developer',
            linguistic_regime='',
            to_dict=Mock(return_value={
                'uuid': str(self.first_uuid),
                'curriculum_year': {
                    'academic_year': 2020,
                    'id': 1,
                },
                'country': BE_ISO_CODE,
                'type': ExperienceType.OTHER_ACTIVITY.name,
                'institute_name': 'UCL',
                'institute_city': 'Louvain-La-Neuve',
                'activity_type': ActivityType.WORK.name,
                'activity_position': 'Developer',
                'linguistic_regime': 'FR',
            })
        )
        mock_second_experience = Mock(
            uuid=self.second_uuid,
            curriculum_year=Mock(
                academic_year=2019,
                id=2,
            ),
            country=BE_ISO_CODE,
            type=ExperienceType.OTHER_ACTIVITY.name,
            institute_name='UCL',
            institute_city='Louvain-La-Neuve',
            activity_type=ActivityType.WORK.name,
            activity_position='Developer',
            linguistic_regime='',
            to_dict=Mock(return_value={
                'uuid': str(self.second_uuid),
                'curriculum_year': {
                    'academic_year': 2019,
                    'id': 2,
                },
                'country': BE_ISO_CODE,
                'type': ExperienceType.OTHER_ACTIVITY.name,
                'institute_name': 'UCL',
                'institute_city': 'Louvain-La-Neuve',
                'activity_type': ActivityType.WORK.name,
                'activity_position': 'Developer',
                'linguistic_regime': 'FR',
            })
        )

        self.mock_person_api.return_value.list_curriculum_experiences_admission.return_value = [
            mock_first_experience,
            mock_second_experience,
        ]

        self.addCleanup(api_person_patcher.stop)

        # Mock academic years api
        academic_years_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_years_api = academic_years_api_patcher.start()

        def get_academic_years(**kwargs):
            years = [
                Mock(year=2020),
                Mock(year=2019),
            ]
            return Mock(results=years)

        self.mock_academic_years_api.return_value.get_academic_years.side_effect = get_academic_years
        self.addCleanup(academic_years_api_patcher.stop)

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
            ]
            if kwargs.get('code'):
                return Mock(results=[c for c in languages if c.code == kwargs.get('code')])
            return Mock(results=languages)

        self.mock_languages_api.return_value.languages_list.side_effect = get_languages
        self.addCleanup(languages_api_patcher.stop)

        # Mock document api
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch('osis_document.api.utils.get_remote_metadata', return_value={'name': 'myfile'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_curriculum_get(self):
        url = resolve_url("admission:doctorate-detail:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)

        self.mock_person_api.return_value.list_curriculum_experiences_admission.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_file_admission.assert_called()
        self.assertContains(response, "2020-2021")

    def test_curriculum_get_form(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.get(url)

        self.mock_person_api.return_value.list_curriculum_experiences_admission.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_file_admission.assert_called()
        self.assertContains(response, "2020-2021")

    def test_curriculum_get_form_with_specified_known_experience(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                          experience_id=self.first_uuid)
        response = self.client.get(url)

        self.mock_person_api.return_value.list_curriculum_experiences_admission.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_file_admission.assert_called()
        self.assertContains(response, "2020-2021")

    def test_curriculum_get_form_with_specified_unknown_experience(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                          experience_id=self.other_uuid)
        response = self.client.get(url)

        self.mock_person_api.return_value.list_curriculum_experiences_admission.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_file_admission.assert_called()
        self.assertContains(response, "2020-2021")

    def test_curriculum_post_upload_file_valid_update(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        response = self.client.post(url, data={
            'curriculum_upload': '',
            'curriculum_upload-curriculum_0': 'uuid1',
        })

        self.mock_person_api.return_value.update_curriculum_file_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            curriculum_file={'curriculum': ['uuid1']},
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_upload_file_valid_create(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        form_prefix = CurriculumForm.CURRICULUM_UPLOAD.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-curriculum_0': 'uuid1',
        })

        self.mock_person_api.return_value.update_curriculum_file.assert_called_with(
            curriculum_file={'curriculum': ['uuid1']},
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_upload_file_invalid_form(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        form_prefix = CurriculumForm.CURRICULUM_UPLOAD.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-curriculum_0': '',
        })

        self.mock_person_api.return_value.update_curriculum_file.assert_not_called()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFormError(response, 'curriculum_upload', 'curriculum', _("This field is required."))

    def test_curriculum_post_upload_file_invalid_request(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        form_prefix = CurriculumForm.CURRICULUM_UPLOAD.value
        self.mock_person_api.return_value.update_curriculum_file.side_effect = ApiException(
            status=500,
        )

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-curriculum_0': 'uuid1',
        })

        self.assertEqual(response.status_code, 200)
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "error")
        self.assertEqual(_("An error has happened when uploading the file."), message.message)

    def test_curriculum_post_create_experience_valid_update(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        form_prefix = CurriculumForm.EXPERIENCE_CREATION.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
            form_prefix + '-dissertation_score': 14.5,
        })

        self.mock_person_api.return_value.create_curriculum_experience_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            experience_input={
                'academic_year': 2020,
                'type': 'OTHER_ACTIVITY',
                'country': 'BE',
                'institute': None,
                'institute_name': 'UCL',
                'institute_postal_code': '',
                'education_name': '',
                'result': '',
                'graduation_year': False,
                'obtained_grade': '',
                'rank_in_diploma': '',
                'issue_diploma_date': None,
                'credit_type': '',
                'entered_credits_number': None,
                'acquired_credits_number': None,
                'transcript': [],
                'graduate_degree': [],
                'access_certificate_after_60_master': [],
                'dissertation_title': '',
                'dissertation_score': '14.5',
                'dissertation_summary': [],
                'belgian_education_community': '',
                'program': None,
                'study_system': '',
                'institute_city': 'Louvain-La-Neuve',
                'study_cycle_type': '',
                'linguistic_regime': None,
                'transcript_translation': [],
                'graduate_degree_translation': [],
                'activity_type': 'ILLNESS',
                'other_activity_type': '',
                'activity_position': '',
                'activity_certificate': ['uuid1'],
            },
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_create_experience_valid_create(self):
        url = resolve_url("admission:doctorate-create:curriculum")

        form_prefix = CurriculumForm.EXPERIENCE_CREATION.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
            form_prefix + '-dissertation_score': 14.5,
        })

        self.mock_person_api.return_value.create_curriculum_experience.assert_called_with(
            experience_input={
                'academic_year': 2020,
                'type': 'OTHER_ACTIVITY',
                'country': 'BE',
                'institute': None,
                'institute_name': 'UCL',
                'institute_postal_code': '',
                'education_name': '',
                'result': '',
                'graduation_year': False,
                'obtained_grade': '',
                'rank_in_diploma': '',
                'issue_diploma_date': None,
                'credit_type': '',
                'entered_credits_number': None,
                'acquired_credits_number': None,
                'transcript': [],
                'graduate_degree': [],
                'access_certificate_after_60_master': [],
                'dissertation_title': '',
                'dissertation_score': '14.5',
                'dissertation_summary': [],
                'belgian_education_community': '',
                'program': None,
                'study_system': '',
                'institute_city': 'Louvain-La-Neuve',
                'study_cycle_type': '',
                'linguistic_regime': None,
                'transcript_translation': [],
                'graduate_degree_translation': [],
                'activity_type': 'ILLNESS',
                'other_activity_type': '',
                'activity_position': '',
                'activity_certificate': ['uuid1'],
            },
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_create_experience_invalid_form(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        form_prefix = CurriculumForm.EXPERIENCE_CREATION.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_certificate_0': 'uuid1',
        })
        self.mock_person_api.return_value.create_curriculum_experience_admission.assert_not_called()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertSubFormError(response, 'creation_form', 'activity_type', _('This field is required.'))

    def test_curriculum_post_create_experience_invalid_request(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        form_prefix = CurriculumForm.EXPERIENCE_CREATION.value
        self.mock_person_api.return_value.create_curriculum_experience.side_effect = ApiException(
            status=500,
        )

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
        })

        self.assertEqual(response.status_code, 200)
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "error")
        self.assertEqual(_("An error has happened when adding the experience."), message.message)

    def test_curriculum_post_update_experience_valid_update(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                          experience_id=self.first_uuid)
        redirect_url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        form_prefix = CurriculumForm.EXPERIENCE_UPDATE.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
        })

        self.mock_person_api.return_value.update_curriculum_experience_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            xp=str(self.first_uuid),
            experience_input={
                'academic_year': 2020,
                'type': 'OTHER_ACTIVITY',
                'country': 'BE',
                'institute': None,
                'institute_name': 'UCL',
                'institute_postal_code': '',
                'education_name': '',
                'result': '',
                'graduation_year': False,
                'obtained_grade': '',
                'rank_in_diploma': '',
                'issue_diploma_date': None,
                'credit_type': '',
                'entered_credits_number': None,
                'acquired_credits_number': None,
                'transcript': [],
                'graduate_degree': [],
                'access_certificate_after_60_master': [],
                'dissertation_title': '',
                'dissertation_score': None,
                'dissertation_summary': [],
                'belgian_education_community': '',
                'program': None,
                'study_system': '',
                'institute_city': 'Louvain-La-Neuve',
                'study_cycle_type': '',
                'linguistic_regime': None,
                'transcript_translation': [],
                'graduate_degree_translation': [],
                'activity_type': 'ILLNESS',
                'other_activity_type': '',
                'activity_position': '',
                'activity_certificate': ['uuid1'],
            },
            **self.api_default_params,
        )
        self.assertRedirects(response, redirect_url)

    def test_curriculum_post_update_experience_valid_create(self):
        url = resolve_url("admission:doctorate-create:curriculum", experience_id=self.first_uuid)
        redirect_url = resolve_url("admission:doctorate-create:curriculum")
        form_prefix = CurriculumForm.EXPERIENCE_UPDATE.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
        })

        self.mock_person_api.return_value.update_curriculum_experience.assert_called_with(
            xp=str(self.first_uuid),
            experience_input={
                'academic_year': 2020,
                'type': 'OTHER_ACTIVITY',
                'country': 'BE',
                'institute': None,
                'institute_name': 'UCL',
                'institute_postal_code': '',
                'education_name': '',
                'result': '',
                'graduation_year': False,
                'obtained_grade': '',
                'rank_in_diploma': '',
                'issue_diploma_date': None,
                'credit_type': '',
                'entered_credits_number': None,
                'acquired_credits_number': None,
                'transcript': [],
                'graduate_degree': [],
                'access_certificate_after_60_master': [],
                'dissertation_title': '',
                'dissertation_score': None,
                'dissertation_summary': [],
                'belgian_education_community': '',
                'program': None,
                'study_system': '',
                'institute_city': 'Louvain-La-Neuve',
                'study_cycle_type': '',
                'linguistic_regime': None,
                'transcript_translation': [],
                'graduate_degree_translation': [],
                'activity_type': 'ILLNESS',
                'other_activity_type': '',
                'activity_position': '',
                'activity_certificate': ['uuid1'],
            },
            **self.api_default_params,
        )
        self.assertRedirects(response, redirect_url)

    def test_curriculum_post_update_experience_invalid_form(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                          experience_id=self.first_uuid)
        form_prefix = CurriculumForm.EXPERIENCE_UPDATE.value

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_certificate_0': 'uuid1',
        })
        self.mock_person_api.return_value.update_curriculum_experience_admission.assert_not_called()
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertSubFormError(response, 'update_form', 'activity_type', _('This field is required.'))

    def test_curriculum_post_update_experience_invalid_request(self):
        url = resolve_url("admission:doctorate-create:curriculum", experience_id=self.first_uuid)
        form_prefix = CurriculumForm.EXPERIENCE_UPDATE.value
        self.mock_person_api.return_value.update_curriculum_experience.side_effect = ApiException(
            status=500,
        )

        response = self.client.post(url, data={
            form_prefix: '',
            form_prefix + '-academic_year': '2020',
            form_prefix + '-country': BE_ISO_CODE,
            form_prefix + '-type': ExperienceType.OTHER_ACTIVITY.name,
            form_prefix + '-activity_institute_name': 'UCL',
            form_prefix + '-activity_institute_city': 'Louvain-La-Neuve',
            form_prefix + '-activity_type': ActivityType.ILLNESS.name,
            form_prefix + '-activity_certificate_0': 'uuid1',
        })

        self.assertEqual(response.status_code, 200)
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "error")
        self.assertEqual(_("An error has happened when updating the experience."), message.message)

    def test_curriculum_post_delete_experience_valid_update(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        response = self.client.post(url, data={
            CurriculumForm.EXPERIENCE_DELETION.value: '',
            'confirmed-id': str(self.first_uuid),
        })

        self.mock_person_api.return_value.destroy_curriculum_experience_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            xp=str(self.first_uuid),
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_delete_experience_valid_create(self):
        url = resolve_url("admission:doctorate-create:curriculum")

        response = self.client.post(url, data={
            CurriculumForm.EXPERIENCE_DELETION.value: '',
            'confirmed-id': str(self.first_uuid),
        })

        self.mock_person_api.return_value.destroy_curriculum_experience.assert_called_with(
            xp=str(self.first_uuid),
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_delete_experience_invalid_request(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        self.mock_person_api.return_value.destroy_curriculum_experience.side_effect = ApiException(
            status=500,
        )
        response = self.client.post(url, data={
            CurriculumForm.EXPERIENCE_DELETION.value: '',
            'confirmed-id': str(self.first_uuid),
        })

        self.mock_person_api.return_value.destroy_curriculum_experience.assert_called_with(
            xp=str(self.first_uuid),
            **self.api_default_params,
        )
        self.assertEqual(response.status_code, 200)
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "error")
        self.assertEqual(_("An error has happened when deleting the experience."), message.message)
