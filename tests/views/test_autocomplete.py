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
import json
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from osis_organisation_sdk.model.address import Address
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites

from admission.tests.utils import MockCity, MockCountry, MockLanguage
from base.tests.factories.person import PersonFactory


class AutocompleteTestCase(TestCase):
    def setUp(self):
        self.client.force_login(PersonFactory().user)

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_doctorate(self, api):
        api.return_value.list_doctorat_dtos.return_value = [
            Mock(sigle='FOOBAR', intitule='Foobar', annee=2021, sigle_entite_gestion="CDE"),
            Mock(sigle='BARBAZ', intitule='Barbaz', annee=2021, sigle_entite_gestion="AZERT"),
        ]
        url = reverse('admission:autocomplete:doctorate')
        response = self.client.get(url, {'forward': json.dumps({'sector': 'SSH'}), 'q': 'foo'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FOOBAR-2021',
                'sigle': 'FOOBAR',
                'sigle_entite_gestion': 'CDE',
                'text': 'FOOBAR - Foobar'
            }],
        })
        self.assertEqual(api.return_value.list_doctorat_dtos.call_args[0], ('SSH',))

    @patch('osis_reference_sdk.api.countries_api.CountriesApi')
    def test_autocomplete_country(self, api):
        api.return_value.countries_list.return_value = Mock(results=[
            MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
            MockCountry(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True),
        ])
        url = reverse('admission:autocomplete:country')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            }, {
                'id': 'BE',
                'text': 'Belgique',
                'european_union': True,
            }]
        })
        api.return_value.countries_list.assert_called()

        api.return_value.countries_list.return_value = Mock(results=[
            MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
        ])
        response = self.client.get(url, {'q': 'F'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            }]
        })
        self.assertEqual(api.return_value.countries_list.call_args[1]['search'], 'F')

    @patch('osis_reference_sdk.api.languages_api.LanguagesApi')
    def test_autocomplete_languages(self, api):
        api.return_value.languages_list.return_value = Mock(results=[
            MockLanguage(code='FR', name='Français', name_en='French'),
            MockLanguage(code='EN', name='Anglais', name_en='English'),
        ])
        url = reverse('admission:autocomplete:language')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'Français'
            }, {
                'id': 'EN',
                'text': 'Anglais'
            }]
        })
        api.return_value.languages_list.assert_called()

        api.return_value.languages_list.return_value = Mock(results=[
            MockLanguage(code='FR', name='Français', name_en='French'),
        ])
        response = self.client.get(url, {'q': 'F'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'Français'
            }]
        })
        self.assertEqual(api.return_value.languages_list.call_args[1]['search'], 'F')

    @patch('osis_reference_sdk.api.cities_api.CitiesApi')
    def test_autocomplete_city(self, api):
        api.return_value.cities_list.return_value = Mock(results=[
            MockCity(name='Pintintin-les-Creumeuil'),
            MockCity(name='Montreuil-les-Sardouille'),
        ])
        url = reverse('admission:autocomplete:city')
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': ''})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'Pintintin-les-Creumeuil',
                'text': 'Pintintin-les-Creumeuil'
            }, {
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille'
            }]
        })
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')

        api.return_value.cities_list.return_value = Mock(results=[
            MockCity(name='Montreuil-les-Sardouille'),
        ])
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': 'Mont'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille'
            }]
        })
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

        # Without the postal code
        response = self.client.get(url, {'forward': json.dumps({'postal_code': ''}), 'q': 'Mont'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille'
            }]
        })
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_tutors(self, api):
        api.return_value.list_tutors.return_value = {'results': [
            Mock(first_name='Michel', last_name='Screugnette', global_id="0123456987"),
            Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
        ]}
        url = reverse('admission:autocomplete:tutor')
        response = self.client.get(url, {'q': 'm'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': '0123456987',
                'text': 'Michel Screugnette',
            }, {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            }],
        })

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_persons(self, api):
        api.return_value.list_persons.return_value = {'results': [
            Mock(first_name='Ripolin', last_name='Trolapois', global_id="0123456987"),
            Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
        ]}
        url = reverse('admission:autocomplete:person')
        response = self.client.get(url, {'q': 'm'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': '0123456987',
                'text': 'Ripolin Trolapois',
            }, {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            }],
        })

    @patch('osis_organisation_sdk.api.entites_api.EntitesApi')
    def test_autocomplete_institute_list(self, api):
        mock_entities = [
            Entite(
                uuid='uuid1',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of technology',
                acronym='IT',
            ),
            Entite(
                uuid='uuid2',
                organization_name='Université Catholique de Louvain',
                organization_acronym='UCL',
                title='Institute of foreign languages',
                acronym='IFL',
            ),
        ]
        api.return_value.get_entities.return_value = PaginatedEntites(
            results=mock_entities,
        )
        url = reverse('admission:autocomplete:institute')
        response = self.client.get(url, {'q': 'Institute'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'uuid1',
                'text': 'Institute of technology (IT)',
            }, {
                'id': 'uuid2',
                'text': 'Institute of foreign languages (IFL)',
            }],
        })

    @patch('osis_organisation_sdk.api.entites_api.EntitesApi')
    def test_autocomplete_institute_location(self, api):
        mock_locations = [
            Address(
                state='Belgique',
                street='Place de l\'université',
                street_number='1',
                postal_code='1348',
                city='Ottignies-Louvain-la-Neuve',
                country_iso_code='BE',
                is_main=True,
            ),
            Address(
                state='Belgique',
                street='Avenue E. Mounier',
                street_number='81',
                postal_code='1200',
                city='Woluwe-Saint-Lambert',
                country_iso_code='BE',
                is_main=True,
            ),
        ]
        # TODO This will become (again) paginated later
        # api.return_value.get_entity_addresses.return_value = PaginatedAddresses(
        #     results=mock_locations,
        #     next=None,
        # )
        api.return_value.get_entity_addresses.return_value = mock_locations[0]
        url = reverse('admission:autocomplete:institute-location')

        response = self.client.get(url, {'forward': json.dumps({'institut_these': ''})}, {'uuid': 'uuid1'})
        self.assertEqual(response.json(), {
            'results': [],
        })

        response = self.client.get(url, {'forward': json.dumps({'institut_these': 'IFL'})}, {'uuid': 'uuid1'})
        self.assertEqual(response.json(), {
            'results': [
                {
                    'id': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                    'text': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                    # }, {
                    #     'id': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
                    #     'text': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
                },
            ],
        })
