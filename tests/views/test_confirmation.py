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

from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ConfirmationTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.detail_url = resolve_url('admission:doctorate-detail:confirm', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        cls.form_url = resolve_url('admission:doctorate-update:confirm', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.mock_proposition_api.return_value.verify_proposition.return_value = Mock().return_value = []
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value = Mock(
            belgian_diploma=None,
            foreign_diploma=None,
        )
        self.addCleanup(person_api_patcher.stop)

    def test_get_without_errors_no_belgian_diploma(self):
        response = self.client.get(self.form_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.assert_called()
        self.mock_proposition_api.return_value.retrieve_proposition.assert_called()
        self.mock_proposition_api.return_value.verify_proposition.assert_called()

        self.assertNotContains(response, _(
            "I authorize the UCLouvain to transmit to the secondary school in which I obtained my CESS, the information"
            " on the success."
        ))
        self.assertContains(
            response, _('Your enrolment can be confirmed as all the necessary conditions have been met.')
        )

    def test_get_without_errors_with_belgian_diploma(self):
        # If the candidate has a belgian diploma, an additional field is displayed
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value = Mock(
            belgian_diploma={
                'academic_graduation_year': 2020,
                'community': 'GERMAN_SPEAKING',
                'educational_other': '',
                'educational_type': '',
                'high_school_diploma': ['fe188a26-5f4e-43fa-83c7-5960497d8009'],
                'high_school_transcript': ['7767f9fc-eaff-414a-88c9-8af18ac21c59'],
                'institute': '',
                'other_institute': 'UCL',
                'result': 'GT_75_RESULT',
                'schedule': None,
            },
            foreign_diploma=None,
        )

        response = self.client.get(self.form_url)

        self.assertContains(response, _(
            "I authorize the UCLouvain to transmit to the secondary school in which I obtained my CESS, the information"
            " on the success."
        ))

    def test_get_with_incomplete_admission(self):
        self.mock_proposition_api.return_value.verify_proposition.return_value = Mock().return_value = [
            Mock(status_code='PROPOSITION-25', detail='Some data is missing.'),
            Mock(status_code='PROPOSITION-39', detail='Every promoter must approve the proposition.'),
        ]

        response = self.client.get(self.form_url)
        # Display an error message as some conditions aren't meet
        self.assertContains(
            response, _('Your enrolment cannot be confirmed. All the following conditions must be met to do it.')
        )
        # Display the missing conditions retrieves by the API
        self.assertContains(
            response, 'Some data is missing.'
        )
        self.assertContains(
            response, 'Every promoter must approve the proposition.'
        )

    def test_post_with_incomplete_form_without_belgian_diploma(self):
        response = self.client.post(self.form_url, data={})

        self.assertEqual(response.status_code, 200)

        for field in [
            'accept_regulations',
            'accept_data_protection_policy',
            'accept_regulated_professions_rules',
            'accept_max_response_time',
        ]:
            self.assertFormError(response, 'form', field, _('This field is required.'))

    def test_post_with_incomplete_form_with_belgian_diploma(self):
        # If the candidate has a belgian diploma, an additional field is required
        self.mock_person_api.return_value.retrieve_high_school_diploma_admission.return_value = Mock(
            belgian_diploma={
                'academic_graduation_year': 2020,
                'community': 'GERMAN_SPEAKING',
                'educational_other': '',
                'educational_type': '',
                'high_school_diploma': ['fe188a26-5f4e-43fa-83c7-5960497d8009'],
                'high_school_transcript': ['7767f9fc-eaff-414a-88c9-8af18ac21c59'],
                'institute': '',
                'other_institute': 'UCL',
                'result': 'GT_75_RESULT',
                'schedule': None,
            },
            foreign_diploma=None,
        )

        response = self.client.post(self.form_url, data={})

        self.assertEqual(response.status_code, 200)

        for field in [
            'accept_regulations',
            'accept_data_protection_policy',
            'accept_regulated_professions_rules',
            'accept_max_response_time',
            'accept_ucl_transfer_information_to_secondary_school',
        ]:
            self.assertFormError(response, 'form', field, _('This field is required.'))

    def test_post_with_complete_form_but_bad_values(self):
        # One checkbox is not checked -> invalid
        response = self.client.post(self.form_url, data={
            'accept_regulations': True,
            'accept_data_protection_policy': False,
            'accept_regulated_professions_rules': True,
            'accept_max_response_time': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'accept_data_protection_policy', _('This field is required.'))

    def test_post_with_complete_form(self):
        # All checkboxes are checked -> valid
        response = self.client.post(self.form_url, data={
            'accept_regulations': True,
            'accept_data_protection_policy': True,
            'accept_regulated_professions_rules': True,
            'accept_max_response_time': True,
        })
        self.assertEqual(response.status_code, 302)
