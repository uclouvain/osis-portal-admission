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
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN

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
        self.continuing_update_url = resolve_url(
            'admission:continuing-education:update:curriculum:professional_update',
            pk=self.continuing_proposition.uuid,
            experience_id=self.professional_experience.uuid,
        )
        self.general_update_url = resolve_url(
            'admission:general-education:update:curriculum:professional_update',
            pk=self.general_proposition.uuid,
            experience_id=self.professional_experience.uuid,
        )
        self.mockapi = self.mock_person_api.return_value

    # On update
    def test_with_admission_on_update_experience_form_is_initialized(self):
        response = self.client.get(self.admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_professional_experience_admission.assert_called()

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
                'valuated_from_trainings': ANY,
            },
        )

    def test_with_admission_on_update_experience_form_is_initialized_with_continuing_education(self):
        response = self.client.get(self.continuing_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_professional_experience_continuing_education_admission.assert_called()

        # Check the context data
        form = response.context.get('form')
        hidden_fields = [f.field for f in form.hidden_fields()]
        self.assertTrue(form.fields['certificate'].disabled)
        self.assertIn(form.fields['certificate'], hidden_fields)

    def test_with_admission_on_update_experience_form_is_initialized_with_general_education(self):
        response = self.client.get(self.general_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the right API calls are done
        self.mockapi.retrieve_professional_experience_general_education_admission.assert_called()

    def test_without_admission_on_update_experience_form_is_not_initialized(self):
        response = self.client.get(self.without_admission_update_url)

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.retrieve_professional_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )

    def test_with_admission_on_update_experience_post_form_empty_data(self):
        response = self.client.post(self.admission_update_url, data={})

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
        self.mockapi.update_professional_experience_admission.assert_not_called()

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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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

    def test_with_admission_on_update_experience_post_form_for_unemployment_with_continuing_education(self):
        response = self.client.post(
            self.continuing_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.UNEMPLOYMENT.name,
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:continuing-education:update:curriculum',
                pk=self.continuing_proposition.uuid,
            )
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_continuing_education_admission.assert_called_once_with(
            uuid=self.continuing_proposition.uuid,
            experience_id=self.professional_experience.uuid,
            professional_experience={
                'start_date': datetime.date(2021, 1, 1),
                'end_date': datetime.date(2022, 1, 31),
                'activity': '',
                'role': '',
                'certificate': ['foobar'],
                'type': ActivityType.UNEMPLOYMENT.name,
                'institute_name': '',
                'sector': '',
            },
            **self.api_default_params,
        )

    def test_with_admission_on_update_experience_post_form_for_unemployment_with_general_education(self):
        response = self.client.post(
            self.general_update_url,
            data={
                **self.all_form_data,
                'type': ActivityType.UNEMPLOYMENT.name,
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url(
                'admission:general-education:update:curriculum',
                pk=self.general_proposition.uuid,
            )
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_general_education_admission.assert_called_once_with(
            uuid=self.general_proposition.uuid,
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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.update_professional_experience_admission.assert_called_once_with(
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

    def test_with_admission_on_update_valuated_experience_is_forbidden(self):
        mock_retrieve = self.mock_person_api.return_value.retrieve_professional_experience_admission
        mock_retrieve.return_value.valuated_from_trainings = ['1']

        response = self.client.get(
            resolve_url(
                self.admission_update_url,
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

        response = self.client.post(
            resolve_url(
                self.admission_update_url,
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
                data=self.all_form_data,
            )
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

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
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mockapi.create_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            professional_experience=ANY,
            **self.api_default_params,
        )

    def test_with_admission_on_create_experience_post_form_for_other_activity_and_redirect_to_editing_page(self):
        self.mockapi.create_professional_experience_admission.return_value = {
            'uuid': self.professional_experience.uuid,
        }

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
            expected_url=resolve_url(
                'admission:doctorate:update:curriculum:professional_update',
                pk=self.proposition.uuid,
                experience_id=self.professional_experience.uuid,
            )
            + '#curriculum-header',
        )

    def test_without_admission_on_create_experience_form_is_not_initialized(self):
        response = self.client.get(resolve_url('admission:create:curriculum:professional_create'))

        # Check the request
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Check that the API calls aren't done
        self.mockapi.retrieve_professional_experience.assert_not_called()
        self.mock_proposition_api.assert_not_called()

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )


class CurriculumNonAcademicExperienceDeleteTestCase(MixinTestCase):
    def test_with_admission_on_delete_experience_post_form(self):
        response = self.client.post(
            resolve_url(
                'admission:doctorate:update:curriculum:professional_delete',
                pk=self.proposition.uuid,
                experience_id=self.professional_experience.uuid,
            ),
            data={
                '_submit_and_continue': True,
            },
        )

        # Check the request
        self.assertRedirects(
            response=response,
            expected_url=resolve_url('admission:doctorate:update:curriculum', pk=self.proposition.uuid)
            + '#non-academic-activities',
        )

        # Check that the API calls are done
        self.mock_person_api.return_value.destroy_professional_experience_admission.assert_called_once_with(
            uuid=self.proposition.uuid,
            experience_id=self.professional_experience.uuid,
            **self.api_default_params,
        )

    def test_with_admission_on_delete_valuated_experience_is_forbidden(self):
        mock_retrieve = self.mock_person_api.return_value.retrieve_professional_experience_admission
        mock_retrieve.return_value.valuated_from_trainings = ['1']

        response = self.client.get(
            resolve_url(
                'admission:doctorate:update:curriculum:professional_delete',
                pk=self.proposition.uuid,
                experience_id=self.educational_experience.uuid,
            )
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

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

        self.assertContains(
            response,
            gettext("You must choose your training before filling in your previous experience."),
        )
