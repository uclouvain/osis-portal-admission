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
import json
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse

from admission.tests.utils import MockCity, MockCountry
from base.tests.factories.user import UserFactory


class AutocompleteTestCase(TestCase):
    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_doctorate(self, api):
        self.client.force_login(UserFactory())
        api.return_value.list_doctorat_dtos.return_value = [
            Mock(sigle='FOOBAR', intitule_fr='Foobar', intitule_en='Foobar', annee=2021, sigle_entite_gestion="CDE"),
            Mock(sigle='BARBAZ', intitule_fr='Barbaz', intitule_en='Barbaz', annee=2021, sigle_entite_gestion="AZERT"),
        ]
        url = reverse('admission:autocomplete:doctorate')
        response = self.client.get(url, {'forward': json.dumps({'sector': 'SSH'}), 'q': 'foo'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FOOBAR-2021',
                'sigle_entite_gestion': 'CDE',
                'text': 'FOOBAR - Foobar'
            }],
        })
        api.return_value.list_doctorat_dtos.assert_called_with("SSH")

    @patch('osis_reference_sdk.api.countries_api.CountriesApi')
    def test_autocomplete_country(self, api):
        self.client.force_login(UserFactory())
        api.return_value.countries_list.return_value = Mock(results=[
            MockCountry(iso_code='FR', name='France', name_en='France'),
            MockCountry(iso_code='BE', name='Belgique', name_en='Belgium'),
        ])
        url = reverse('admission:autocomplete:country')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'France'
            }, {
                'id': 'BE',
                'text': 'Belgique'
            }]
        })
        api.return_value.countries_list.assert_called_with()

        api.return_value.countries_list.return_value = Mock(results=[
            MockCountry(iso_code='FR', name='France', name_en='France'),
        ])
        response = self.client.get(url, {'q': 'F'})
        self.assertEqual(response.json(), {
            'results': [{
                'id': 'FR',
                'text': 'France'
            }]
        })
        api.return_value.countries_list.assert_called_with(search="F")

    @patch('osis_reference_sdk.api.cities_api.CitiesApi')
    def test_autocomplete_city(self, api):
        self.client.force_login(UserFactory())
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
        api.return_value.cities_list.assert_called_with(zip_code='1111')

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
        api.return_value.cities_list.assert_called_with(zip_code='1111', search="Mont")
