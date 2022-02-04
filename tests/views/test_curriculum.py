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
from unittest.mock import patch, Mock, ANY

from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from osis_admission_sdk import ApiException
from osis_admission_sdk.model.experience_output_country import ExperienceOutputCountry
from osis_admission_sdk.model.experience_output_curriculum_year import ExperienceOutputCurriculumYear
from rest_framework import status
from rest_framework.status import HTTP_200_OK

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.curriculum import ExperienceType, ActivityType
from admission.contrib.views.form_tabs.curriculum import CurriculumForm
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

        mock_experience = Mock(
            id=1,
            curriculum_year=Mock(
                academic_year=2020,
                id=1,
            ),
            country=Mock(
                iso_code=BE_ISO_CODE,
                name='Belgium',
            ),
            type=ExperienceType.OTHER_ACTIVITY.name,
            institute_name='UCL',
            institute_city='Louvain-La-Neuve',
            activity_type=ActivityType.WORK.name,
            activity_position='Developer',
            to_dict=Mock(return_value={
                'id': 1,
                'curriculum_year': {
                    'academic_year': 2020,
                    'id': 1,
                },
                'country': {
                    'iso_code': BE_ISO_CODE,
                    'name': 'Belgium',
                },
                'type': ExperienceType.OTHER_ACTIVITY.name,
                'institute_name': 'UCL',
                'institute_city': 'Louvain-La-Neuve',
                'activity_type': ActivityType.WORK.name,
                'activity_position': 'Developer',

            })
        )

        self.mock_person_api.return_value.list_curriculum_experiences_admission.return_value = [
            mock_experience,
        ]

        self.addCleanup(api_person_patcher.stop)

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
                          experience_id=1)
        response = self.client.get(url)

        self.mock_person_api.return_value.list_curriculum_experiences_admission.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_file_admission.assert_called()
        self.assertContains(response, "2020-2021")

    def test_curriculum_get_form_with_specified_unknown_experience(self):
        url = resolve_url("admission:doctorate-update:curriculum", pk="3c5cdc60-2537-4a12-a396-64d2e9e34876",
                          experience_id=2)
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
            status=404,
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
            status=404,
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
                          experience_id=1)
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
            xp='1',
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
        url = resolve_url("admission:doctorate-create:curriculum", experience_id=1)
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
            xp='1',
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
                          experience_id=1)
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
        url = resolve_url("admission:doctorate-create:curriculum", experience_id=1)
        form_prefix = CurriculumForm.EXPERIENCE_UPDATE.value
        self.mock_person_api.return_value.update_curriculum_experience.side_effect = ApiException(
            status=404,
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
            'confirmed-id': '1',
        })

        self.mock_person_api.return_value.destroy_curriculum_experience_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            xp='1',
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_delete_experience_valid_create(self):
        url = resolve_url("admission:doctorate-create:curriculum")

        response = self.client.post(url, data={
            CurriculumForm.EXPERIENCE_DELETION.value: '',
            'confirmed-id': '1',
        })

        self.mock_person_api.return_value.destroy_curriculum_experience.assert_called_with(
            xp='1',
            **self.api_default_params,
        )
        self.assertRedirects(response, url)

    def test_curriculum_post_delete_experience_invalid_request(self):
        url = resolve_url("admission:doctorate-create:curriculum")
        self.mock_person_api.return_value.destroy_curriculum_experience.side_effect = ApiException(
            status=404,
        )
        response = self.client.post(url, data={
            CurriculumForm.EXPERIENCE_DELETION.value: '',
            'confirmed-id': '1',
        })

        self.mock_person_api.return_value.destroy_curriculum_experience.assert_called_with(
            xp='1',
            **self.api_default_params,
        )
        self.assertEqual(response.status_code, 200)
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, "error")
        self.assertEqual(_("An error has happened when deleting the experience."), message.message)
