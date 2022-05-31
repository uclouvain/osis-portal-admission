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
from django.shortcuts import resolve_url
from rest_framework.status import HTTP_200_OK

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.tests.views.curriculum.mixin import MixinTestCase


class GlobalCurriculumTestCase(MixinTestCase):
    def setUp(self):
        super().setUp()
        self.admission_read_url = resolve_url('admission:doctorate:curriculum', pk=self.proposition.uuid)
        self.admission_update_url = resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
        self.create_url = resolve_url('admission:doctorate-create:curriculum')

    def test_on_create_curriculum_is_loaded(self):
        response = self.client.get(self.create_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_person_api.return_value.retrieve_curriculum.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('curriculum_file'), self.curriculum_file)
        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

    def test_with_admission_on_reading_curriculum_is_loaded(self):
        response = self.client.get(self.admission_read_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('curriculum_file'), self.curriculum_file)
        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

    def test_with_admission_on_update_curriculum_is_loaded(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called()
        self.mock_person_api.return_value.retrieve_curriculum_admission.assert_called()

        # Check the context data
        self.assertEqual(len(response.context.get('professional_experiences')), 1)
        self.assertEqual(response.context.get('professional_experiences')[0], self.lite_professional_experience)

        self.assertEqual(len(response.context.get('educational_experiences')), 1)
        self.assertEqual(response.context.get('educational_experiences')[0], self.lite_educational_experience)

        self.assertEqual(response.context.get('curriculum_file'), self.curriculum_file)
        self.assertEqual(response.context.get('minimal_year'), self.academic_year_2020.year)

        self.assertEqual(response.context.get('form').initial['curriculum'], self.curriculum_file.get('curriculum'))

    def test_on_create_post_curriculum_file(self):
        response = self.client.post(
            self.create_url,
            data={
                'curriculum_0': ['f1.pdf'],
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate-create:curriculum'),
        )

        # Check that the right API calls are done
        self.mock_person_api.return_value.update_curriculum_file.assert_called_once_with(
            curriculum_file={
                'curriculum': ['f1.pdf'],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_curriculum_file(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'curriculum_0': ['f1.pdf'],
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the right API calls are done
        self.mock_person_api.return_value.update_curriculum_file_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            curriculum_file={
                'curriculum': ['f1.pdf'],
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_post_without_curriculum_file_returns_error(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'curriculum_0': [],
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls are not done
        self.mock_person_api.return_value.update_curriculum_file_admission.assert_not_called()

        # Check the context data
        self.assertFormError(response=response, form='form', field='curriculum', errors=FIELD_REQUIRED_MESSAGE)
