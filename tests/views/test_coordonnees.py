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
from django.test import TestCase

from admission.tests.utils import MockCountry
from base.tests.factories.person import PersonFactory
from osis_admission_sdk.model.coordonnees import Coordonnees
from osis_admission_sdk.model.coordonnees_contact import CoordonneesContact


class CoordonneesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        self.addCleanup(person_api_patcher.stop)

        self.mock_person_api.return_value.retrieve_coordonnees.return_value = Coordonnees._from_openapi_data(
            email="john@example.org",
            phone_mobile="",
            residential=CoordonneesContact(
                location="",
                postal_code="",
                city="",
                country="",
                street="",
                street_number="",
                postal_box="",
                place="",
            ),
            contact=CoordonneesContact(
                location="",
                postal_code="",
                city="",
                country="",
                street="",
                street_number="",
                postal_box="",
                place="",
            ),
        )

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        def get_countries(**kwargs):
            countries = [
                MockCountry(iso_code='FR', name='France', name_en='France'),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium'),
            ]
            if kwargs.get('iso_code'):
                return Mock(results=[c for c in countries if c.iso_code == kwargs.get('iso_code')])
            if kwargs.get('name'):
                return Mock(results=[c for c in countries if c.name == kwargs.get('name')])
            return Mock(results=countries)

        self.mock_countries_api.return_value.countries_list.side_effect = get_countries
        self.addCleanup(countries_api_patcher.stop)

        academic_year_api_patcher = patch("osis_reference_sdk.api.academic_years_api.AcademicYearsApi")
        self.mock_academic_year_api = academic_year_api_patcher.start()
        self.addCleanup(academic_year_api_patcher.stop)
        autocomplete_api_patcher = patch("frontoffice.settings.osis_sdk.utils.get_user_token")
        mock_user_token = autocomplete_api_patcher.start()
        mock_user_token.return_value = 'foobar'
        self.addCleanup(mock_user_token.stop)

    def test_form_display(self):
        url = resolve_url('admission:doctorate-create:coordonnees')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.mock_person_api.return_value.retrieve_coordonnees.assert_called()
        self.mock_proposition_api.assert_not_called()

    def test_form_empty(self):
        url = resolve_url('admission:doctorate-create:coordonnees')

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        self.mock_person_api.return_value.update_coordonnees.assert_called()

    def test_form_should_be_all_filled(self):
        url = resolve_url('admission:doctorate-create:coordonnees')

        response = self.client.post(url, {
            "residential-country": "FR",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('city', response.context['residential'].errors)

    def test_form_belgian(self):
        url = resolve_url('admission:doctorate-create:coordonnees')

        response = self.client.post(url, {
            "residential-country": "BE",
            "residential-be_postal_code": "1111",
            "residential-be_city": "Louvain-La-Neuve",
            "residential-street": "Rue du Compas",
            "residential-street_number": "1",
        })
        self.assertEqual(response.status_code, 302)
        last_call = self.mock_person_api.return_value.update_coordonnees.mock_calls[-1]
        self.assertEqual(last_call.kwargs['coordonnees']['residential']['postal_code'], "1111")
        self.assertEqual(last_call.kwargs['coordonnees']['residential']['city'], "Louvain-La-Neuve")

    def test_update(self):
        url = resolve_url('admission:doctorate-update:coordonnees', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        self.mock_person_api.return_value.retrieve_coordonnees.return_value['residential']['country'] = "BE"
        self.mock_person_api.return_value.retrieve_coordonnees.return_value['contact']['country'] = "BE"
        self.mock_person_api.return_value.retrieve_coordonnees.return_value['contact']['city'] = "Liège"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belgique")
        self.mock_person_api.return_value.retrieve_coordonnees.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)

    def test_detail(self):
        url = resolve_url('admission:doctorate-detail:coordonnees', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        self.mock_person_api.return_value.retrieve_coordonnees.return_value = Mock(
            residential=Mock(country=""),
            contact=Mock(country="", attribute_map={}),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Belgique")
        self.mock_person_api.return_value.retrieve_coordonnees.assert_called()
        self.assertIn('admission', response.context)

        self.mock_person_api.return_value.retrieve_coordonnees.return_value = Mock(
            residential=Mock(country="FR"),
            contact=Mock(country="BE", attribute_map={"country": "BE"}),
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belgique")
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_coordonnees.assert_called()
        self.assertIn('admission', response.context)
