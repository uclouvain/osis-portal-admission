# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest import mock
from unittest.mock import Mock, patch

from django.shortcuts import resolve_url
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums import ChoixStatutPropositionDoctorale
from admission.tests.utils import MockCountry
from base.tests.factories.person import PersonFactory
from base.tests.test_case import OsisPortalTestCase


class CoordonneesTestCase(OsisPortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()

    def setUp(self):
        self.client.force_login(self.person.user)

        propositions_api_patcher = patch("osis_admission_sdk.api.propositions_api.PropositionsApi")
        self.mock_proposition_api = propositions_api_patcher.start()
        self.addCleanup(propositions_api_patcher.stop)

        self.mock_proposition_api.return_value.detail_proposition_create_permissions.return_value = mock.Mock(
            links={
                'create_coordinates': {'url': 'foobar'},
            }
        )

        person_api_patcher = patch("osis_admission_sdk.api.person_api.PersonApi")
        self.mock_person_api = person_api_patcher.start()
        self.addCleanup(person_api_patcher.stop)

        self.mock_get = (
            self.mock_person_api.return_value.retrieve_coordonnees.return_value.to_dict
        ) = self.mock_person_api.return_value.retrieve_coordonnees_admission.return_value.to_dict
        self.mock_get.return_value = dict(
            email="john@example.org",
            phone_mobile="",
            residential={
                'postal_code': "",
                'city': "",
                'country': "",
                'street': "",
                'street_number': "",
                'postal_box': "",
            },
            contact={
                'postal_code': "",
                'city': "",
                'country': "",
                'street': "",
                'street_number': "",
                'postal_box': "",
            },
        )

        countries_api_patcher = patch("osis_reference_sdk.api.countries_api.CountriesApi")
        self.mock_countries_api = countries_api_patcher.start()

        def get_countries(**kwargs):
            countries = [
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True),
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

    def test_form_with_submitted_admission_is_not_readonly(self):
        url = resolve_url('admission:create:coordonnees')
        self.client.force_login(self.person.user)

        self.mock_proposition_api.return_value.detail_proposition_create_permissions.return_value = mock.Mock(
            links={
                'create_coordinates': {'error': 'foobar'},
            }
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'admission/details/coordonnees.html')
        self.assertTemplateUsed(response, 'admission/forms/coordonnees.html')

    def test_form_display(self):
        url = resolve_url('admission:create:coordonnees')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'admission/details/coordonnees.html')
        self.assertTemplateUsed(response, 'admission/forms/coordonnees.html')
        self.mock_person_api.return_value.retrieve_coordonnees.assert_called()

        # Some fields are disabled if they are already set
        form = response.context['main_form']
        self.assertFalse(form.fields['private_email'].disabled)

        self.mock_get.return_value['private_email'] = 'john@example.org'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['main_form']
        self.assertTrue(form.fields['private_email'].disabled)

    def test_form_empty(self):
        url = resolve_url('admission:create:coordonnees')

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertIn('city', response.context['residential'].errors)
        self.mock_person_api.return_value.update_coordonnees.assert_not_called()

    def test_form_should_be_all_filled(self):
        url = resolve_url('admission:create:coordonnees')

        response = self.client.post(
            url,
            {
                "residential-country": "FR",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('city', response.context['residential'].errors)
        self.assertIn('phone_mobile', response.context['main_form'].errors)

    def test_form_belgian(self):
        url = resolve_url('admission:create:coordonnees')

        response = self.client.post(
            url,
            {
                "residential-country": "BE",
                "residential-be_postal_code": "1111",
                "residential-be_city": "Louvain-La-Neuve",
                "residential-street": "Rue du Compas",
                "residential-street_number": "1",
                "private_email": "john@example.org",
                "phone_mobile": "+32474123456",
            },
        )
        self.assertEqual(response.status_code, 302)
        last_call_kwargs = self.mock_person_api.return_value.update_coordonnees.call_args[1]
        self.assertEqual(last_call_kwargs['coordonnees']['residential']['postal_code'], "1111")
        self.assertEqual(last_call_kwargs['coordonnees']['residential']['city'], "Louvain-La-Neuve")
        self.assertEqual(last_call_kwargs['coordonnees']['private_email'], "john@example.org")
        self.assertIsNone(last_call_kwargs['coordonnees']['contact'])
        self.assertEqual(last_call_kwargs['coordonnees']['phone_mobile'], "+32474123456")

    def test_form_foreign_with_contact_address(self):
        url = resolve_url('admission:create:coordonnees')

        self.mock_get.return_value['private_email'] = 'john@example.org'

        response = self.client.post(
            url,
            {
                "residential-country": "FR",
                "residential-postal_code": "44000",
                "residential-city": "Nantes",
                "residential-street": "Rue du Compas",
                "residential-street_number": "1",
                "contact-country": "FR",
                "contact-postal_code": "44001",
                "contact-city": "Nantes",
                "contact-street": "Rue du Compas",
                "contact-street_number": "2",
                "show_contact": True,
                "private_email": "john_2@example.org",  # Will be overwritten as it is already set
                "phone_mobile": "+32474123456",
                "emergency_contact_phone": "+32474123457",
            },
        )
        self.assertEqual(response.status_code, 302)
        last_call_kwargs = self.mock_person_api.return_value.update_coordonnees.call_args[1]
        self.assertEqual(
            last_call_kwargs["coordonnees"]["contact"],
            {
                "country": "FR",
                "postal_code": "44001",
                "city": "Nantes",
                "street": "Rue du Compas",
                "street_number": "2",
                "postal_box": "",
            },
        )
        self.assertEqual(last_call_kwargs["coordonnees"]["private_email"], 'john@example.org')
        self.assertEqual(last_call_kwargs["coordonnees"]["phone_mobile"], '+32474123456')
        self.assertEqual(last_call_kwargs["coordonnees"]["emergency_contact_phone"], '+32474123457')

    def test_update(self):
        url = resolve_url('admission:doctorate:update:coordonnees', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")
        self.mock_proposition_api.return_value.retrieve_doctorate_proposition.return_value = Mock(
            statut=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
            links={},
            erreurs=[],
        )

        self.mock_get.return_value['residential']['country'] = "BE"
        self.mock_get.return_value['contact']['country'] = "BE"
        self.mock_get.return_value['contact']['city'] = "Liège"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Save and continue"))
        self.assertContains(response, '<form class="osis-form"')
        self.assertContains(response, "Belgique")
        self.mock_person_api.return_value.retrieve_coordonnees_admission.assert_called()
        self.mock_proposition_api.assert_called()
        self.assertIn('admission', response.context)

        valid_data = {
            "residential-country": "BE",
            "residential-be_postal_code": "1111",
            "residential-be_city": "Louvain-La-Neuve",
            "residential-street": "Rue du Compas",
            "residential-street_number": "1",
            'private_email': 'john@example.org',
            'phone_mobile': '+32474123456',
        }

        response = self.client.post(
            url,
            {
                **valid_data,
                'phone_mobile': "1234567890",  # Not in international format
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(_('Invalid phone number'), form.errors.get('phone_mobile', []))

        response = self.client.post(
            url,
            {
                **valid_data,
                'phone_mobile': "+324741234560",  # Too long
            },
        )

        self.assertEqual(response.status_code, 200)

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn(_('Invalid phone number'), form.errors.get('phone_mobile', []))

        response = self.client.post(url, valid_data)
        self.assertEqual(response.status_code, 302)

    def test_detail(self):
        url = resolve_url('admission:doctorate:coordonnees', pk="3c5cdc60-2537-4a12-a396-64d2e9e34876")

        self.mock_get.return_value = {'residential': None, 'contact': None}
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.mock_get.return_value = {'residential': {'country': ""}, 'contact': {'country': ""}}

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Belgique")
        self.mock_person_api.return_value.retrieve_coordonnees_admission.assert_called()
        self.mock_person_api.return_value.retrieve_coordonnees_admission.resetMock()
        self.assertIn('admission', response.context)

        self.mock_get.return_value = {'residential': {'country': "FR"}, 'contact': {'country': "BE"}}

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Belgique")
        self.assertContains(response, "France")
        self.mock_person_api.return_value.retrieve_coordonnees_admission.assert_called()
        self.assertIn('admission', response.context)
