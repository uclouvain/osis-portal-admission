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
import datetime
from unittest.mock import Mock, patch, ANY

import freezegun
from django.shortcuts import resolve_url
from django.test import TestCase, override_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from admission.constants import BE_ISO_CODE
from admission.contrib.enums.person import CivilState
from admission.contrib.forms import PDF_MIME_TYPE
from admission.tests import get_paginated_years
from admission.tests.utils import MockCountry
from base.tests.factories.person import PersonFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
@freezegun.freeze_time('2023-01-01')
class PersonViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.default_kwargs = {
            'accept_language': ANY,
            'x_user_first_name': ANY,
            'x_user_last_name': ANY,
            'x_user_email': ANY,
            'x_user_global_id': ANY,
        }

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
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True),
            ]
            if kwargs.get('iso_code'):
                return Mock(results=[c for c in countries if c.iso_code == kwargs.get('iso_code')])
            return Mock(results=countries)

        self.mock_countries_api.return_value.countries_list.side_effect = get_countries
        self.addCleanup(countries_api_patcher.stop)

        self.current_year = datetime.date.today().year

        # Mock document api
        patcher = patch('osis_document.api.utils.get_remote_token', return_value='foobar')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={'name': 'myfile', 'mimetype': PDF_MIME_TYPE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.mock_academic_year_api.return_value.get_academic_years.return_value = get_paginated_years(
            self.current_year - 2,
            self.current_year + 2,
        )

        self.addCleanup(academic_year_api_patcher.stop)

    def test_form(self):
        url = resolve_url('admission:create:person')
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
        self.assertContains(response, "osis-document.umd.min.js", count=1)
        self.assertContains(response, "dependsOn.min.js", count=1)
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')
        self.assertEqual(response.context['form'].initial['unknown_birth_date'], True)
        self.assertIsNone(response.context['form'].initial.get('has_national_number'))
        self.assertEqual(response.context['form'].initial['identification_type'], '')
        self.mock_person_api.return_value.retrieve_person_identification.assert_called()
        self.mock_proposition_api.assert_not_called()

        response = self.client.post(
            url,
            {
                'first_name': "Joe",
                'last_name': "Doe",
                'sex': 'M',
                'gender': 'X',
                'civil_state': CivilState.MARRIED.name,
                'birth_country': 'BE',
                'birth_place': 'Louvain-la-Neuve',
                'birth_date': datetime.date(1990, 1, 1),
                'has_national_number': True,
                'national_number': '01234567890',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification.assert_called()

    def test_form_redirect_with_continue(self):
        self.client.force_login(self.person.user)

        self.mock_person_api.return_value.retrieve_person_identification.return_value.to_dict.return_value = dict(
            first_name="John",
            last_name="Doe",
            id_card=[],
            passport=[],
            id_photo=[],
            birth_year="1990",
        )
        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()
        self.addCleanup(countries_api_patcher.stop)

        response = self.client.post(
            resolve_url('admission:create:person'),
            {
                'first_name': "Joe",
                'last_name': "Doe",
                'sex': 'M',
                'gender': 'X',
                'civil_state': CivilState.MARRIED.name,
                'birth_country': 'BE',
                'birth_place': 'Louvain-la-Neuve',
                'birth_date': datetime.date(1990, 1, 1),
                '_submit_and_continue': '',
                'has_national_number': True,
                'national_number': '01234567890',
            },
        )

        self.assertRedirects(response, resolve_url('admission:create:coordonnees'))

    def test_update(self):
        url = resolve_url('admission:doctorate:update:person', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        mocking_dict = self.mock_person_api.return_value.retrieve_person_identification_admission.return_value
        mocking_dict.to_dict.return_value = dict(
            first_name="John",
            last_name="Doe",
            id_card=[],
            passport=[],
            id_photo=[],
            birth_country="BE",
            country_of_citizenship="FR",
            last_registration_year=2021,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "John")
        self.assertContains(response, "FR")
        self.assertContains(response, "BE")
        self.mock_person_api.return_value.retrieve_person_identification_admission.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

        response = self.client.post(
            url,
            {
                'unknown_birth_date': True,
                'country_of_citizenship': "BE",
                'already_registered': True,
                'civil_state': CivilState.MARRIED.name,
                'birth_country': 'BE',
                'birth_place': 'Louvain-la-Neuve',
                'id_card_number': '0123456789',
                'passport_number': '0123456789',
                'last_registration_id': '0123456A',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFormError(response, 'form', 'birth_year', _("This field is required."))
        self.assertFormError(response, 'form', 'last_registration_year', _("This field is required."))
        self.assertFormError(response, 'form', 'last_registration_id', _("This field is required."))
        self.assertFormError(response, 'form', 'first_name', _("This field is required if the last name is missing."))
        self.assertFormError(response, 'form', 'last_name', _("This field is required if the first name is missing."))
        self.assertFormError(response, 'form', 'last_registration_id', _("The NOMA must contain 8 digits."))

    def test_post_update(self):
        url = resolve_url('admission:doctorate:update:person', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        mocking_dict = self.mock_person_api.return_value.retrieve_person_identification_admission.return_value
        mocking_dict.to_dict.return_value = dict(
            first_name="John",
            last_name="Doe",
            id_card=[],
            passport=[],
            id_photo=[],
            birth_country="BE",
            country_of_citizenship="FR",
            last_registration_year=2021,
            resides_in_belgium=False,
        )

        data = {
            'first_name': "JOE",
            'last_name': "DOE",
            'middle_name': 'JIM,JoHN,Jean-PiERRE',
            'birth_date': datetime.date(2022, 5, 1),
            'civil_state': CivilState.MARRIED.name,
            'birth_country': 'BE',
            'birth_place': 'LOUvain-la-Neuve',
            'birth_year': 1990,
            'sex': 'M',
            'gender': 'X',
            'last_registration_year': self.current_year - 2,
            'last_registration_id': '12345678',
            'has_national_number': False,
            'identification_type': 'PASSPORT_NUMBER',
            'passport_number': '0123456789',
            'passport_0': 'test',
            'national_number': '01234567890',
            'id_card_0': 'test',
            'id_card_number': '0123456789',
        }

        person_kwargs = {
            'first_name': 'Joe',
            'middle_name': 'Jim,John,Jean-Pierre',
            'last_name': 'Doe',
            'first_name_in_use': '',
            'sex': 'M',
            'gender': 'X',
            'birth_year': 1990,
            'civil_state': CivilState.MARRIED.name,
            'birth_country': 'BE',
            'birth_place': 'Louvain-la-Neuve',
            'country_of_citizenship': '',
            'language': '',
            'id_card': [],
            'passport': ['test'],
            'national_number': '',
            'id_card_number': '',
            'passport_number': '0123456789',
            'id_photo': [],
            'last_registration_year': self.current_year - 2,
            'last_registration_id': '12345678',
            'birth_date': datetime.date(2022, 5, 1),
        }

        response = self.client.post(
            url,
            {
                **data,
                'unknown_birth_date': True,
                'already_registered': False,
                'has_national_number': True,
                'identification_type': 'PASSPORT_NUMBER',
                'passport_number': '0123456789',
                'passport_0': 'test',
                'national_number': '01234567890',
                'id_card_0': 'test',
                'id_card_number': '0123456789',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            person_identification={
                **person_kwargs,
                'id_card': ['test'],
                'national_number': '01234567890',
                # Clean some fields depending on other fields values
                'birth_date': None,
                'last_registration_year': None,
                'last_registration_id': '',
                'passport': [],
                'passport_number': '',
                'id_card_number': '',
            },
            **self.default_kwargs,
        )

        response = self.client.post(
            url,
            {
                **data,
                'unknown_birth_date': False,
                'already_registered': True,
                'identification_type': 'ID_CARD_NUMBER',
                'passport_number': '0123456789',
                'passport_0': 'test',
                'national_number': '01234567890',
                'id_card_0': 'test',
                'id_card_number': '0123456789',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            person_identification={
                **person_kwargs,
                'id_card': ['test'],
                'id_card_number': '0123456789',
                # Clean some fields depending on other fields values
                'birth_year': None,
                'passport': [],
                'passport_number': '',
                'national_number': '',
            },
            **self.default_kwargs,
        )

        response = self.client.post(
            url,
            {
                **data,
                'unknown_birth_date': True,
                'already_registered': False,
                'has_national_number': False,
                'identification_type': 'PASSPORT_NUMBER',
                'passport_number': '0123456789',
                'passport_0': 'test',
                'national_number': '01234567890',
                'id_card_0': 'test',
                'id_card_number': '0123456789',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            person_identification={
                **person_kwargs,
                'passport': ['test'],
                'passport_number': '0123456789',
                # Clean some fields depending on other fields values
                'birth_date': None,
                'last_registration_year': None,
                'last_registration_id': '',
                'id_card': [],
                'id_card_number': '',
                'national_number': '',
            },
            **self.default_kwargs,
        )

        mocking_dict.to_dict.return_value['resides_in_belgium'] = True

        response = self.client.post(
            url,
            {
                **data,
                'country_of_citizenship': BE_ISO_CODE,
                'unknown_birth_date': True,
                'already_registered': False,
                'has_national_number': False,
                'identification_type': 'PASSPORT_NUMBER',
                'passport_number': '0123456789',
                'passport_0': 'test',
                'national_number': '01234567890',
                'id_card_0': 'test',
                'id_card_number': '0123456789',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.mock_person_api.return_value.update_person_identification_admission.assert_called_with(
            uuid='3c5cdc60-2537-4a12-a396-64d2e9e34876',
            person_identification={
                **person_kwargs,
                'country_of_citizenship': BE_ISO_CODE,
                'id_card': ['test'],
                'national_number': '01234567890',
                # Clean some fields depending on other fields values
                'birth_date': None,
                'last_registration_year': None,
                'last_registration_id': '',
                'passport': [],
                'passport_number': '',
                'id_card_number': '',
            },
            **self.default_kwargs,
        )

    def test_detail(self):
        url = resolve_url('admission:doctorate:person', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.client.force_login(self.person.user)

        mocking_dict_return = self.mock_person_api.return_value.retrieve_person_identification_admission.return_value
        mocking_dict_return.to_dict.return_value = dict(
            first_name="Joe",
            birth_country="",
            country_of_citizenship="",
            birth_date=datetime.date(1990, 1, 1),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "osis-document.umd.min.js", count=1)
        self.assertContains(response, "Joe")
        self.mock_person_api.return_value.retrieve_person_identification_admission.assert_called()
        self.assertIn('admission', response.context)

        mocking_dict_return.to_dict.return_value = dict(
            first_name="John",
            birth_country="BE",
            country_of_citizenship="FR",
            birth_date=datetime.date(1990, 1, 1),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "John")
        self.assertContains(response, "Belgique")
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_person_identification_admission.assert_called()
        self.assertIn('admission', response.context)
