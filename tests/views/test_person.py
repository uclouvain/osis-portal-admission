# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from admission.tests.utils import MockCountry
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class PersonViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
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

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.addCleanup(academic_year_api_patcher.stop)

    def test_form(self):
        url = resolve_url('admission:doctorate-create:person')
        self.client.force_login(self.person.user)

        self.mock_person_api.return_value.retrieve_person_identification.return_value.to_dict.return_value = dict(
            first_name="John",
            last_name="Doe",
            id_card=[],
            passport=[],
            id_photo=[],
            birth_year="1990",
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.context['form'].initial['unknown_birth_date'], True)
        self.mock_person_api.return_value.retrieve_person_identification.assert_called()
        self.mock_proposition_api.assert_not_called()

        response = self.client.post(url, {
            'first_name': "Joe",
            'last_name': "Doe",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification.assert_called()

    def test_update(self):
        url = resolve_url('admission:doctorate-update:person', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        values = dict(
            first_name="John",
            last_name="Doe",
            id_card=[],
            passport=[],
            id_photo=[],
            birth_country="BE",
            country_of_citizenship="FR",
            last_registration_year=2021,
        )
        self.mock_person_api.return_value.retrieve_person_identification.return_value = Mock(**values)
        self.mock_person_api.return_value.retrieve_person_identification.return_value.to_dict.return_value = values

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "John")
        self.assertContains(response, "FR")
        self.assertContains(response, "BE")
        self.mock_person_api.return_value.retrieve_person_identification.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

        response = self.client.post(url, {
            'first_name': "Joe",
            'last_name': "Doe",
            'unknown_birth_date': True,
            'already_registered': 'YES',
            'passport_number': 'ABC123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'birth_year', _("This field is required."))
        self.assertFormError(response, 'form', 'last_registration_year', _("This field is required."))
        self.assertFormError(response, 'form', 'passport_expiration_date', _("This field is required."))

        response = self.client.post(url, {
            'first_name': "Joe",
            'last_name': "Doe",
            'passport_expiration_date': '22/11/2021',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'passport_number', _("This field is required."))

        response = self.client.post(url, {
            'first_name': "Joe",
            'last_name': "Doe",
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_detail(self):
        url = resolve_url('admission:doctorate-detail:person', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        self.mock_person_api.return_value.retrieve_person_identification.return_value = Mock(
            first_name="Joe",
            birth_country="",
            country_of_citizenship="",
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Joe")
        self.mock_person_api.return_value.retrieve_person_identification.assert_called()
        self.assertIn('admission', response.context)

        self.mock_person_api.return_value.retrieve_person_identification.return_value = Mock(
            first_name="John",
            birth_country="BE",
            country_of_citizenship="FR",
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "John")
        self.assertContains(response, "Belgique")
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_person_identification.assert_called()
        self.assertIn('admission', response.context)
