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
from unittest.mock import ANY

from django.shortcuts import resolve_url
from django.utils.translation import gettext
from rest_framework.status import HTTP_200_OK

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.curriculum import ActivityType, ActivitySector
from admission.tests.views.curriculum.mixin import MixinTestCase


class CurriculumNonAcademicExperienceReadTestCase(MixinTestCase):
    def test_with_admission_on_reading_experience_is_loaded(self):
        response = self.client.get(
            resolve_url(
                'admission:doctorate:curriculum:professional_read',
                pk=self.proposition.uuid,
                experience_id=self.professional_experience.uuid,
            )
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_person_api.return_value.retrieve_professional_experience_admission.assert_called()

        # Check the context data
        self.assertEqual(response.context.get('experience'), self.professional_experience)


class CurriculumNonAcademicExperienceFormTestCase(MixinTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.default_form_data = {
            'start_date_month': 1,
            'start_date_year': 2021,
            'end_date_month': 1,
            'end_date_year': 2022,
        }

        cls.all_form_data = {
            **cls.default_form_data,
            'activity': 'Activity name',
            'type': ActivityType.WORK.name,
            'role': 'Librarian',
            'sector': ActivitySector.PUBLIC.name,
            'institute_name': 'UCL',
            'certificate_0': ['f1.pdf'],
        }

    def setUp(self):
        super().setUp()
        self.admission_update_url = resolve_url(
            'admission:doctorate:update:curriculum:professional_update',
            pk=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
        )
        self.without_admission_update_url = resolve_url(
            'admission:create:curriculum:professional_update',
            experience_id=self.professional_experience.uuid,
        )

    # On update
    def test_with_admission_on_update_experience_form_is_initialized(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mock_person_api.return_value.retrieve_professional_experience_admission.assert_called()

        # Check the context data
        self.assertEqual(
            response.context.get('form').initial,
            {
                'start_date_month': int(self.professional_experience.start_date.month),
                'end_date_month': int(self.professional_experience.end_date.month),
                'start_date_year': int(self.professional_experience.start_date.year),
                'end_date_year': int(self.professional_experience.end_date.year),
                'type': self.professional_experience.type.value,
                'role': self.professional_experience.role,
                'sector': self.professional_experience.sector.value,
                'institute_name': self.professional_experience.institute_name,
                'certificate': self.professional_experience.certificate,
                'activity': self.professional_experience.activity,
                'uuid': self.professional_experience.uuid,
            },
        )

    def test_without_admission_on_update_experience_form_is_not_initialized(self):
        response = self.client.get(self.without_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.retrieve_professional_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertTrue(
            gettext("You must choose your training before filling in your previous experience."),
            response.content.decode("utf-8"),
        )

    def test_with_admission_on_update_experience_post_form_empty_data(self):
        response = self.client.post(self.admission_update_url, data={})

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['form'].errors), 5)
        for field in [
            'start_date_month',
            'end_date_month',
            'start_date_year',
            'end_date_year',
            'type',
        ]:
            self.assertFormError(response, 'form', field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_missing_fields_for_work(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.default_form_data,
                'type': ActivityType.WORK.name,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['form'].errors), 3)
        for field in [
            'role',
            'sector',
            'institute_name',
        ]:
            self.assertFormError(response, 'form', field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_missing_fields_for_internship(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.default_form_data,
                'type': ActivityType.INTERNSHIP.name,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['form'].errors), 2)
        for field in [
            'sector',
            'institute_name',
        ]:
            self.assertFormError(response, 'form', field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_missing_fields_for_volunteering(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.default_form_data,
                'type': ActivityType.VOLUNTEERING.name,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['form'].errors), 2)
        for field in [
            'sector',
            'institute_name',
        ]:
            self.assertFormError(response, 'form', field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_missing_fields_for_other_activity(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.default_form_data,
                'type': ActivityType.OTHER.name,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertEqual(len(response.context['form'].errors), 1)
        for field in [
            'activity',
        ]:
            self.assertFormError(response, 'form', field, errors=FIELD_REQUIRED_MESSAGE)

    def test_with_admission_on_update_experience_post_form_bad_years(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'start_date_month': 1,
                'start_date_year': 2021,
                'end_date_month': 1,
                'end_date_year': 2020,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(
            response=response,
            form='form',
            field=None,
            errors=gettext("The start date must be equals or lower than the end date."),
        )

    def test_with_admission_on_update_experience_post_form_bad_months(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                'start_date_month': 2,
                'start_date_year': 2020,
                'end_date_month': 1,
                'end_date_year': 2020,
            },
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_not_called()

        # Check the context data
        self.assertFormError(
            response=response,
            form='form',
            field=None,
            errors=gettext("The start date must be equals or lower than the end date."),
        )

    def test_with_admission_on_update_experience_post_form_for_work(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.WORK.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': 'Librarian',
                'certificate': ['f1.pdf'],
                'type': ActivityType.WORK.name,
                'institute_name': 'UCL',
                'sector': ActivitySector.PUBLIC.name,
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_internship(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.INTERNSHIP.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': '',
                'certificate': ['f1.pdf'],
                'type': ActivityType.INTERNSHIP.name,
                'institute_name': 'UCL',
                'sector': ActivitySector.PUBLIC.name,
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_volunteering(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.VOLUNTEERING.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': '',
                'certificate': ['f1.pdf'],
                'type': ActivityType.VOLUNTEERING.name,
                'institute_name': 'UCL',
                'sector': ActivitySector.PUBLIC.name,
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_unemployment(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.UNEMPLOYMENT.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': '',
                'certificate': ['f1.pdf'],
                'type': ActivityType.UNEMPLOYMENT.name,
                'institute_name': '',
                'sector': '',
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_language_travel(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.LANGUAGE_TRAVEL.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': '',
                'certificate': ['f1.pdf'],
                'type': ActivityType.LANGUAGE_TRAVEL.name,
                'institute_name': '',
                'sector': '',
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_other_activity(self):
        response = self.client.post(
            self.admission_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.OTHER.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.update_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': 'Activity name',
                'role': '',
                'certificate': [],
                'type': ActivityType.OTHER.name,
                'institute_name': '',
                'sector': '',
            },
            **self.api_default_params,
        )

    # On create
    def test_with_admission_on_create_experience_post_form_for_other_activity(self):
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:professional_create',
                pk=self.proposition.uuid,
            ),
            data={
                **self.all_form_data,
                'type': ActivityType.OTHER.name,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.create_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            professional_experience=ANY,
            **self.api_default_params,
        )

    def test_without_admission_on_create_experience_form_is_not_initialized(self):
        response = self.client.get(resolve_url('admission:create:curriculum:professional_create'))

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.retrieve_professional_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertTrue(
            gettext("You must choose your training before filling in your previous experience."),
            response.content.decode("utf-8"),
        )


class CurriculumNonAcademicExperienceDeleteTestCase(MixinTestCase):
    def test_with_admission_on_delete_experience_post_form(self):
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:professional_delete',
                pk=self.proposition.uuid,
                experience_id=self.professional_experience.uuid,
            )
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid),
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.destroy_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            **self.api_default_params,
        )

    def test_without_admission_on_delete_experience_form_is_not_initialized(self):
        response = self.client.get(
            resolve_url(
                'admission:create:curriculum:professional_delete',
                experience_id=self.professional_experience.uuid,
            ),
        )

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mock_person_api.return_value.retrieve_professional_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertTrue(
            gettext("You must choose your training before filling in your previous experience."),
            response.content.decode("utf-8"),
        )
