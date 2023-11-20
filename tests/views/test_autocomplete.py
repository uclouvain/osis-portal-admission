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

import json
import uuid
from unittest.mock import ANY, Mock, patch

from django.test import TestCase
from django.urls import reverse
from osis_admission_sdk.model.diplomatic_post import DiplomaticPost
from osis_admission_sdk.model.doctorat_dto import DoctoratDTO
from osis_admission_sdk.model.formation_continue_dto import FormationContinueDTO
from osis_admission_sdk.model.formation_generale_dto import FormationGeneraleDTO
from osis_admission_sdk.model.scholarship import Scholarship
from osis_organisation_sdk.model.address import Address
from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.paginated_entites import PaginatedEntites
from osis_reference_sdk.model.diploma import Diploma
from osis_reference_sdk.model.high_school import HighSchool
from osis_reference_sdk.model.paginated_diploma import PaginatedDiploma
from osis_reference_sdk.model.paginated_high_school import PaginatedHighSchool
from osis_reference_sdk.model.paginated_superior_non_university import PaginatedSuperiorNonUniversity
from osis_reference_sdk.model.paginated_university import PaginatedUniversity
from osis_reference_sdk.model.superior_non_university import SuperiorNonUniversity
from osis_reference_sdk.model.university import University
from waffle.testutils import override_switch

from admission.contrib.enums import BelgianCommunitiesOfEducation, TypeFormationChoisissable
from admission.contrib.enums.diploma import StudyType
from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.training_choice import TrainingType, TypeFormation
from admission.tests.utils import MockCity, MockCountry, MockLanguage
from base.tests.factories.person import PersonFactory

DEFAULT_API_PARAMS = {
    'accept_language': ANY,
    'x_user_first_name': ANY,
    'x_user_last_name': ANY,
    'x_user_email': ANY,
    'x_user_global_id': ANY,
}


class AutocompleteTestCase(TestCase):
    def setUp(self):
        self.client.force_login(PersonFactory().user)

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_doctorate(self, api):
        api.return_value.list_doctorat_dtos.return_value = [
            DoctoratDTO(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                sigle_entite_gestion="CDE",
                campus="Louvain-La-Neuve",
                type=TrainingType.PHD.name,
                campus_inscription='Mons',
            ),
        ]
        url = reverse('admission:autocomplete:doctorate')
        response = self.client.get(url, {'forward': json.dumps({'sector': 'SSH'}), 'q': 'foo'})
        results = [
            {
                'id': 'FOOBAR-2021',
                'sigle': 'FOOBAR',
                'sigle_entite_gestion': 'CDE',
                'text': 'Foobar (Louvain-La-Neuve) <span class="training-acronym">FOOBAR</span>',
            }
        ]
        self.assertDictEqual(response.json(), {'results': results})
        api.return_value.list_doctorat_dtos.assert_called_with(
            acronym_or_name='foo',
            sigle='SSH',
            campus='',
            **DEFAULT_API_PARAMS,
        )

    @patch('osis_reference_sdk.api.countries_api.CountriesApi')
    def test_autocomplete_country(self, api):
        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
                MockCountry(iso_code='BE', name='Belgique', name_en='Belgium', european_union=True),
            ]
        )
        url = reverse('admission:autocomplete:country')
        response = self.client.get(url, {'q': ''})
        expected = [
            {
                'id': 'BE',
                'text': 'Belgique',
                'european_union': True,
            },
            {
                'id': None,
                'text': '<hr>',
            },
            {
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            },
            {
                'id': 'BE',
                'text': 'Belgique',
                'european_union': True,
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected, 'pagination': {'more': False}})
        api.return_value.countries_list.assert_called()

        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
            ]
        )
        response = self.client.get(url, {'q': 'F'})
        expected = [
            {
                'id': 'FR',
                'text': 'France',
                'european_union': True,
            }
        ]
        self.assertDictEqual(response.json(), {'results': expected, 'pagination': {'more': False}})
        self.assertEqual(api.return_value.countries_list.call_args[1]['search'], 'F')

        api.return_value.countries_list.return_value = Mock(
            results=[
                MockCountry(iso_code='FR', name='France', name_en='France', european_union=True),
            ]
            * 20
        )
        url = reverse('admission:autocomplete:country')
        response = self.client.get(url)
        results = response.json()
        self.assertEqual(len(results['results']), 22)
        self.assertIs(results['pagination']['more'], True)
        api.return_value.countries_list.assert_called()

    @patch('osis_reference_sdk.api.languages_api.LanguagesApi')
    def test_autocomplete_languages(self, api):
        api.return_value.languages_list.return_value = Mock(
            results=[
                MockLanguage(code='FR', name='Français', name_en='French'),
                MockLanguage(code='EN', name='Anglais', name_en='English'),
            ]
        )
        url = reverse('admission:autocomplete:language')
        response = self.client.get(url, {'q': ''})
        expected = [
            {
                'id': 'FR',
                'text': 'Français',
            },
            {
                'id': 'EN',
                'text': 'Anglais',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})
        api.return_value.languages_list.assert_called()

        api.return_value.languages_list.return_value = Mock(
            results=[
                MockLanguage(code='FR', name='Français', name_en='French'),
            ]
        )
        response = self.client.get(url, {'q': 'F'})
        expected = [
            {
                'id': 'FR',
                'text': 'Français',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})
        self.assertEqual(api.return_value.languages_list.call_args[1]['search'], 'F')

    @patch('osis_reference_sdk.api.cities_api.CitiesApi')
    def test_autocomplete_city(self, api):
        api.return_value.cities_list.return_value = Mock(
            results=[
                MockCity(name='Pintintin-les-Creumeuil'),
                MockCity(name='Montreuil-les-Sardouille'),
            ]
        )
        url = reverse('admission:autocomplete:city')
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': ''})
        expected = [
            {
                'id': 'Pintintin-les-Creumeuil',
                'text': 'Pintintin-les-Creumeuil',
            },
            {
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')

        api.return_value.cities_list.return_value = Mock(
            results=[
                MockCity(name='Montreuil-les-Sardouille'),
            ]
        )
        response = self.client.get(url, {'forward': json.dumps({'postal_code': '1111'}), 'q': 'Mont'})
        expected = [
            {
                'id': 'Montreuil-les-Sardouille',
                'text': 'Montreuil-les-Sardouille',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['zip_code'], '1111')
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

        # Without the postal code
        response = self.client.get(url, {'forward': json.dumps({'postal_code': ''}), 'q': 'Mont'})
        self.assertDictEqual(response.json(), {'results': expected})
        self.assertEqual(api.return_value.cities_list.call_args[1]['search'], 'Mont')

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_tutors(self, api):
        api.return_value.list_tutors.return_value = {
            'results': [
                Mock(first_name='Michel', last_name='Screugnette', global_id="0123456987"),
                Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
            ]
        }
        url = reverse('admission:autocomplete:tutor')
        response = self.client.get(url, {'q': 'm'})
        expected = [
            {
                'id': '0123456987',
                'text': 'Michel Screugnette',
            },
            {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_persons(self, api):
        api.return_value.list_persons.return_value = {
            'results': [
                Mock(first_name='Ripolin', last_name='Trolapois', global_id="0123456987"),
                Mock(first_name='Marie-Odile', last_name='Troufignon', global_id="789654213"),
            ]
        }
        url = reverse('admission:autocomplete:person')
        response = self.client.get(url, {'q': 'm'})
        expected = [
            {
                'id': '0123456987',
                'text': 'Ripolin Trolapois',
            },
            {
                'id': '789654213',
                'text': 'Marie-Odile Troufignon',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

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
        expected = [
            {
                'id': 'uuid1',
                'text': 'Institute of technology (IT)',
            },
            {
                'id': 'uuid2',
                'text': 'Institute of foreign languages (IFL)',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

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
        self.assertDictEqual(response.json(), {'results': []})

        response = self.client.get(url, {'forward': json.dumps({'institut_these': 'IFL'})}, {'uuid': 'uuid1'})
        expected = [
            {
                'id': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                'text': 'Place de l\'université 1, 1348 Ottignies-Louvain-la-Neuve, Belgique',
                # }, {
                #     'id': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
                #     'text': 'Avenue E. Mounier 81, 1200 Woluwe-Saint-Lambert, Belgique',
            },
        ]
        self.assertDictEqual(response.json(), {'results': expected})

    @patch('osis_reference_sdk.api.high_schools_api.HighSchoolsApi')
    def test_autocomplete_high_school_list(self, api):
        self.first_high_school_uuid = str(uuid.uuid4())
        self.second_high_school_uuid = str(uuid.uuid4())
        self.maxDiff = None

        mock_schools = [
            HighSchool(
                uuid=self.first_high_school_uuid,
                name="HighSchool 1",
                city="Louvain-La-Neuve",
                zipcode="1348",
                street="Place de l'Université",
                street_number="1",
            ),
            HighSchool(
                uuid=self.second_high_school_uuid,
                name="HighSchool 2",
                city="Bruxelles",
                zipcode="1000",
                street="Boulevard du Triomphe",
                street_number="1",
            ),
        ]
        api.return_value.high_schools_list.return_value = PaginatedHighSchool(
            results=mock_schools,
        )
        url = reverse('admission:autocomplete:high-school')
        response = self.client.get(url, {'q': 'HighSchool'})

        api.return_value.high_schools_list.assert_called_with(
            limit=20,
            offset=0,
            search='HighSchool',
            active=True,
            **DEFAULT_API_PARAMS,
        )

        expected = [
            {
                'id': self.first_high_school_uuid,
                'text': 'HighSchool 1 <span class="school-address">Place de l\'Université 1, '
                '1348 Louvain-La-Neuve</span>',
            },
            {
                'id': self.second_high_school_uuid,
                'text': 'HighSchool 2 <span class="school-address">Boulevard du Triomphe 1, 1000 Bruxelles</span>',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

        # With speaking community filter
        response = self.client.get(
            url,
            {
                'q': 'HighSchool',
                'forward': json.dumps({'community': BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name}),
            },
        )

        api.return_value.high_schools_list.assert_called_with(
            limit=20,
            offset=0,
            search='HighSchool',
            active=True,
            linguistic_regime=BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name,
            **DEFAULT_API_PARAMS,
        )

        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_reference_sdk.api.diplomas_api.DiplomasApi')
    def test_autocomplete_diploma_list(self, api):
        self.first_diploma_uuid = str(uuid.uuid4())
        self.second_diploma_uuid = str(uuid.uuid4())

        mock_diplomas = [
            Diploma(uuid=self.first_diploma_uuid, title="Computer science"),
            Diploma(uuid=self.second_diploma_uuid, title="Human sciences"),
        ]
        api.return_value.diplomas_list.return_value = PaginatedDiploma(
            results=mock_diplomas,
        )
        url = reverse('admission:autocomplete:diploma')
        response = self.client.get(url, {'q': 'science'})
        expected = [
            {
                'id': self.first_diploma_uuid,
                'text': 'Computer science',
            },
            {
                'id': self.second_diploma_uuid,
                'text': 'Human sciences',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_learning_unit_sdk.api.learning_units_api.LearningUnitsApi')
    def test_autocomplete_learning_unit_year(self, api):
        api.return_value.learningunits_list.return_value = {
            'results': [
                dict(acronym="ESA2004", title="dumb text"),
                dict(acronym="ESA2006", title="dumb text 2"),
            ]
        }
        url = reverse('admission:autocomplete:learning-unit-years')
        response = self.client.get(url, {'q': 'ES', 'forward': json.dumps({'academic_year': '2021'})})
        expected = [
            {'id': "ESA2004", 'text': "ESA2004 - dumb text"},
            {'id': "ESA2006", 'text': "ESA2006 - dumb text 2"},
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_scholarship(self, api):
        first_scholarship_uuid = str(uuid.uuid4())
        second_scholarship_uuid = str(uuid.uuid4())

        mock_scholarships = [
            Scholarship._from_openapi_data(
                uuid=first_scholarship_uuid,
                short_name="EM-1",
                long_name="Erasmus Mundus 1",
                type=TypeBourse.ERASMUS_MUNDUS.name,
            ),
            Scholarship._from_openapi_data(
                uuid=second_scholarship_uuid,
                short_name="EM-2",
                long_name="",
                type=TypeBourse.ERASMUS_MUNDUS.name,
            ),
        ]

        api.return_value.list_scholarships.return_value = {
            'results': mock_scholarships,
        }
        url = reverse('admission:autocomplete:scholarship')

        response = self.client.get(
            url, {'q': 'Erasmus', 'forward': json.dumps({'type': TypeBourse.ERASMUS_MUNDUS.name})}
        )
        expected = [
            {'id': first_scholarship_uuid, 'text': "Erasmus Mundus 1"},
            {'id': second_scholarship_uuid, 'text': "EM-2"},
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_general_education_training(self, api):
        api.return_value.list_formation_generale_dtos.return_value = [
            FormationGeneraleDTO(
                sigle='FOOBAR',
                intitule='Foobar',
                annee=2021,
                campus="Louvain-La-Neuve",
                type=TrainingType.MASTER_M1.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMG',
                code='FOOBAR',
            ),
            FormationGeneraleDTO(
                sigle='BARBAZ',
                intitule='Barbaz',
                annee=2021,
                campus="Mons",
                type=TrainingType.MASTER_M1.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMG',
                code='BARBAZ',
            ),
        ]
        url = reverse('admission:autocomplete:general-education')
        response = self.client.get(
            url, {'forward': json.dumps({'training_type': TypeFormation.MASTER.name}), 'q': 'ar'}
        )
        results = [
            {
                'id': 'FOOBAR-2021',
                'text': 'Foobar (Louvain-La-Neuve) <span class="training-acronym">FOOBAR</span>',
            },
            {
                'id': 'BARBAZ-2021',
                'text': 'Barbaz (Mons) <span class="training-acronym">BARBAZ</span>',
            },
        ]
        self.assertDictEqual(response.json(), {'results': results})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    @override_switch('admission-iufc', active=True)
    def test_autocomplete_mixed_education_training(self, api):
        api.return_value.list_formation_continue_dtos.return_value = [
            FormationContinueDTO(
                sigle='CONFOOBAR',
                intitule='Foobar',
                annee=2021,
                campus="Louvain-La-Neuve",
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMC',
                code='CONFOOBAR',
            ),
            FormationContinueDTO(
                sigle='CONBARBAZ',
                intitule='Barbaz',
                annee=2021,
                campus="Mons",
                type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMC',
                code='CONBARBAZ',
            ),
        ]
        api.return_value.list_formation_generale_dtos.return_value = [
            FormationGeneraleDTO(
                sigle='GENFOOBAR',
                intitule='Foobar',
                annee=2021,
                campus="Louvain-La-Neuve",
                type=TrainingType.CERTIFICATE.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMG',
                code='GENFOOBAR',
            ),
            FormationGeneraleDTO(
                sigle='GENBARBAZ',
                intitule='Barbaz',
                annee=2021,
                campus="Mons",
                type=TrainingType.CERTIFICATE.name,
                code_domaine='10C',
                campus_inscription='Mons',
                sigle_entite_gestion='CMG',
                code='GENBARBAZ',
            ),
        ]
        url = reverse('admission:autocomplete:mixed-training')
        data = {
            'forward': json.dumps({'training_type': TypeFormationChoisissable.CERTIFICAT_ATTESTATION.name}),
            'q': 'ar',
        }
        response = self.client.get(url, data)
        results = [
            {
                'id': 'CONFOOBAR-2021',
                'text': 'Foobar (Louvain-La-Neuve) <span class="training-acronym">CONFOOBAR</span>',
            },
            {'id': 'CONBARBAZ-2021', 'text': 'Barbaz (Mons) <span class="training-acronym">CONBARBAZ</span>'},
            {
                'id': 'GENFOOBAR-2021',
                'text': 'Foobar (Louvain-La-Neuve) <span class="training-acronym">GENFOOBAR</span>',
            },
            {'id': 'GENBARBAZ-2021', 'text': 'Barbaz (Mons) <span class="training-acronym">GENBARBAZ</span>'},
        ]
        self.assertDictEqual(response.json(), {'results': results})

    @patch('osis_reference_sdk.api.superior_non_universities_api.SuperiorNonUniversitiesApi')
    def test_autocomplete_non_universities_list(self, api):
        self.first_superior_school_uuid = str(uuid.uuid4())
        self.second_superior_school_uuid = str(uuid.uuid4())

        mock_schools = [
            SuperiorNonUniversity(
                url='',
                uuid=self.first_superior_school_uuid,
                name="Superior 1",
                acronym="S1",
                city="Louvain-La-Neuve",
                zipcode="1348",
                street="Place de l'Université",
                street_number="1",
            ),
            SuperiorNonUniversity(
                url='',
                uuid=self.second_superior_school_uuid,
                name="Superior 2",
                acronym="S1",
                city="Bruxelles",
                zipcode="1000",
                street="Boulevard du Triomphe",
                street_number="1",
            ),
        ]
        api.return_value.superior_non_universities_list.return_value = PaginatedSuperiorNonUniversity(
            results=mock_schools,
        )
        url = reverse('admission:autocomplete:superior-non-university')
        response = self.client.get(url, {'q': 'Superior'})

        api.return_value.superior_non_universities_list.assert_called_with(
            limit=20,
            offset=0,
            search='Superior',
            active=True,
            **DEFAULT_API_PARAMS,
        )

        expected = [
            {
                'id': self.first_superior_school_uuid,
                'text': 'Superior 1',
            },
            {
                'id': self.second_superior_school_uuid,
                'text': 'Superior 2',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

        # With speaking community filter
        response = self.client.get(
            url,
            {
                'q': 'Superior',
                'forward': json.dumps({'country': 'FR'}),
            },
        )

        api.return_value.superior_non_universities_list.assert_called_with(
            limit=20,
            offset=0,
            search='Superior',
            active=True,
            country_iso_code='FR',
            **DEFAULT_API_PARAMS,
        )

        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_reference_sdk.api.universities_api.UniversitiesApi')
    def test_autocomplete_universities_list(self, api):
        self.first_superior_school_uuid = str(uuid.uuid4())
        self.second_superior_school_uuid = str(uuid.uuid4())

        mock_schools = [
            University(
                url='',
                uuid=self.first_superior_school_uuid,
                name="Superior 1",
                acronym="S1",
                city="Louvain-La-Neuve",
                zipcode="1348",
                street="Place de l'Université",
                street_number="1",
            ),
            University(
                url='',
                uuid=self.second_superior_school_uuid,
                name="Superior 2",
                acronym="S1",
                city="Bruxelles",
                zipcode="1000",
                street="Boulevard du Triomphe",
                street_number="1",
            ),
        ]
        api.return_value.universities_list.return_value = PaginatedUniversity(
            results=mock_schools,
        )
        url = reverse('admission:autocomplete:university')
        response = self.client.get(url, {'q': 'Superior'})

        api.return_value.universities_list.assert_called_with(
            limit=20,
            offset=0,
            search='Superior',
            active=True,
            **DEFAULT_API_PARAMS,
        )

        expected = [
            {
                'id': self.first_superior_school_uuid,
                'text': 'Superior 1',
            },
            {
                'id': self.second_superior_school_uuid,
                'text': 'Superior 2',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

        # With speaking community filter
        response = self.client.get(
            url,
            {
                'q': 'Superior',
                'forward': json.dumps({'country': 'FR'}),
            },
        )

        api.return_value.universities_list.assert_called_with(
            limit=20,
            offset=0,
            search='Superior',
            active=True,
            country_iso_code='FR',
            **DEFAULT_API_PARAMS,
        )

        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_reference_sdk.api.superior_non_universities_api.SuperiorNonUniversitiesApi')
    @patch('osis_reference_sdk.api.universities_api.UniversitiesApi')
    def test_autocomplete_superior_list(self, api_university, api_non_university):
        self.first_superior_school_uuid = str(uuid.uuid4())
        self.second_superior_school_uuid = str(uuid.uuid4())
        self.third_superior_school_uuid = str(uuid.uuid4())
        self.fourth_superior_school_uuid = str(uuid.uuid4())

        mock_universities = [
            University(
                url='',
                uuid=self.first_superior_school_uuid,
                name="Superior 2",
                acronym="S2",
                city="Louvain-La-Neuve",
                zipcode="1348",
                street="Place de l'Université",
                street_number="2",
            ),
            University(
                url='',
                uuid=self.second_superior_school_uuid,
                name="Superior 3",
                acronym="S3",
                city="Bruxelles",
                zipcode="1000",
                street="Boulevard du Triomphe",
                street_number="1",
            ),
        ]
        api_university.return_value.universities_list.return_value = PaginatedUniversity(
            count=2,
            results=mock_universities,
        )
        mock_non_universities = [
            SuperiorNonUniversity(
                url='',
                uuid=self.third_superior_school_uuid,
                name="Superior 1",
                acronym="S1",
                city="Louvain-La-Neuve",
                zipcode="1348",
                street="Place de l'Université",
                street_number="3",
            ),
            SuperiorNonUniversity(
                url='',
                uuid=self.fourth_superior_school_uuid,
                name="Superior 4",
                acronym="S4",
                city="Bruxelles",
                zipcode="1000",
                street="Boulevard du Triomphe",
                street_number="4",
            ),
        ]
        self.maxDiff = None
        api_non_university.return_value.superior_non_universities_list.return_value = PaginatedSuperiorNonUniversity(
            count=2,
            results=mock_non_universities,
        )
        url = reverse('admission:autocomplete:superior-institute')
        response = self.client.get(url, {'q': 'Superior'})

        api_non_university.return_value.superior_non_universities_list.assert_called_with(
            limit=18,
            offset=0,
            search='Superior',
            active=True,
            **DEFAULT_API_PARAMS,
        )

        expected = [
            {
                'id': self.third_superior_school_uuid,
                'text': 'Superior 1'
                ' <span class="school-address">Place de l\'Université 3, 1348 Louvain-La-Neuve</span>',
                'type': StudyType.NON_UNIVERSITY.name,
            },
            {
                'id': self.first_superior_school_uuid,
                'text': 'Superior 2'
                ' <span class="school-address">Place de l\'Université 2, 1348 Louvain-La-Neuve</span>',
                'type': StudyType.UNIVERSITY.name,
            },
            {
                'id': self.second_superior_school_uuid,
                'text': 'Superior 3 <span class="school-address">Boulevard du Triomphe 1, 1000 Bruxelles</span>',
                'type': StudyType.UNIVERSITY.name,
            },
            {
                'id': self.fourth_superior_school_uuid,
                'text': 'Superior 4 <span class="school-address">Boulevard du Triomphe 4, 1000 Bruxelles</span>',
                'type': StudyType.NON_UNIVERSITY.name,
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

    @patch('osis_admission_sdk.api.autocomplete_api.AutocompleteApi')
    def test_autocomplete_diplomatic_post(self, api):
        self.first_diplomatic_post_code = 1
        self.second_diplomatic_post_code = 2
        self.third_diplomatic_post_code = 3

        api.return_value.list_diplomatic_posts.return_value = {
            'results': [
                DiplomaticPost._new_from_openapi_data(
                    code=self.first_diplomatic_post_code,
                    name_fr='Marseille',
                    name_en='Marseille',
                    email='marseille@example.be',
                    countries_iso_codes=['FR'],
                ),
                DiplomaticPost._new_from_openapi_data(
                    code=self.second_diplomatic_post_code,
                    name_fr='Paris',
                    name_en='Paris',
                    email='paris@example.be',
                    countries_iso_codes=['FR', 'GF'],
                ),
                DiplomaticPost._new_from_openapi_data(
                    code=self.third_diplomatic_post_code,
                    name_fr='Londres',
                    name_en='London',
                    email='london@example.be',
                    countries_iso_codes=['GB'],
                ),
            ]
        }
        url = reverse('admission:autocomplete:diplomatic-post')
        response = self.client.get(url, {'q': 'a'})

        expected = [
            {
                'id': self.first_diplomatic_post_code,
                'text': 'Marseille',
            },
            {
                'id': self.second_diplomatic_post_code,
                'text': 'Paris',
            },
            {
                'id': self.third_diplomatic_post_code,
                'text': 'Londres',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})

        url = reverse('admission:autocomplete:diplomatic-post')

        response = self.client.get(url, {'q': 'a', 'forward': json.dumps({'residential_country': 'FR'})})

        expected = [
            {
                'id': self.first_diplomatic_post_code,
                'text': 'Marseille',
            },
            {
                'id': self.second_diplomatic_post_code,
                'text': 'Paris',
            },
            {
                'id': None,
                'text': '<hr>',
            },
            {
                'id': self.third_diplomatic_post_code,
                'text': 'Londres',
            },
        ]
        self.assertDictEqual(response.json(), {'pagination': {'more': False}, 'results': expected})
