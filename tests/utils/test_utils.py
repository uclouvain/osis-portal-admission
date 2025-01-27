# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.test import TestCase
from osis_organisation_sdk.model.address import Address
from osis_organisation_sdk.model.entite import Entite

from admission.contrib.enums.scholarship import TypeBourse
from admission.contrib.enums.training_choice import TrainingType
from admission.utils import *
from osis_admission_sdk.model.doctorat_dto import DoctoratDTO
from osis_admission_sdk.model.formation_continue_dto import FormationContinueDTO
from osis_admission_sdk.model.formation_generale_dto import FormationGeneraleDTO
from osis_admission_sdk.model.scholarship import Scholarship


class UtilsTestCase(TestCase):
    def setUp(self) -> None:
        self.address = Address(
            city="Louvain-la-Neuve",
            street="Route de Blocry",
            street_number="5",
            postal_code="1348",
            state="Belgique",
        )
        self.entity = Entite(
            uuid='uuid',
            organization_name='Université Catholique de Louvain',
            organization_acronym='UCL',
            title='Institute of technology',
            acronym='IT',
        )

    def test_format_entity_name(self):
        """Return the concatenation of the entity name and acronym."""
        self.assertEqual(
            format_entity_title(entity=self.entity),
            '{title} ({acronym})'.format_map(self.entity),
        )

    def test_format_address_with_street_and_city_and_state_parts(self):
        """Return the concatenation of the street number, street, postal code, city and state if they are defined"""
        self.assertEqual(
            format_entity_address(address=self.address),
            '{street} {street_number}, {postal_code} {city}, {state}'.format_map(self.address),
        )

    def test_format_address_with_city_and_state_parts(self):
        """Return the concatenation of the postal code, city and state if they are defined"""
        address = Address(
            city=self.address.city,
            street="",
            street_number="",
            postal_code=self.address.postal_code,
            state=self.address.state,
        )
        self.assertEqual(
            format_entity_address(address=address),
            '{postal_code} {city}, {state}'.format_map(address),
        )

    def test_format_address_with_state_part(self):
        """Return the state if it is the only part of the address which is defined"""
        address = Address(
            city="",
            street="",
            street_number="",
            postal_code="",
            state=self.address.state,
        )
        self.assertEqual(
            format_entity_address(address=address),
            '{state}'.format_map(address),
        )

    def test_force_title_empty_string(self):
        result = force_title('')
        self.assertEqual(result, '')

    def test_force_title_uppercase_string_single_word(self):
        result = force_title('FRÉDÉRIC')
        self.assertEqual(result, 'Frédéric')

    def test_force_title_uppercase_string_several_words_separated_by_spaces(self):
        result = force_title('FRÉDÉRIC DE LOUVAIN')
        self.assertEqual(result, 'Frédéric De Louvain')

    def test_force_title_string_several_words_separated_by_spaces(self):
        result = force_title('Frédéric de LouVAIN')
        self.assertEqual(result, 'Frédéric de Louvain')

    def test_force_title_string_several_words_separated_by_commas(self):
        result = force_title('Pierre,pAUL,JACQUES')
        self.assertEqual(result, 'Pierre,paul,Jacques')

    def test_format_training_for_continuing_education(self):
        formation = FormationContinueDTO(
            sigle='INFO-1',
            campus='Mons',
            intitule='Certificat en informatique',
            intitule_en='Computer science certificate',
            intitule_fr='Certificat en informatique',
            annee=2020,
            type=TrainingType.CERTIFICATE_OF_PARTICIPATION.name,
            code_domaine='10C',
            sigle_entite_gestion='CMC',
            campus_inscription='Mons',
            code='INFO-1',
        )
        self.assertEqual(
            format_training(formation),
            'Certificat en informatique (Mons) <span class="training-acronym">INFO-1</span>',
        )

    def test_format_training_for_general_education(self):
        formation = FormationGeneraleDTO(
            sigle='INFO-1',
            campus='Mons',
            intitule='Master en informatique',
            intitule_en='Computer science master',
            intitule_fr='Master en informatique',
            annee=2020,
            type=TrainingType.MASTER_M1.name,
            code_domaine='10C',
            sigle_entite_gestion='CMG',
            campus_inscription='Mons',
            code='INFO-1',
        )
        self.assertEqual(
            format_training(formation),
            'Master en informatique (Mons) <span class="training-acronym">INFO-1</span>',
        )

    def test_format_training_with_year_for_doctorate(self):
        formation = DoctoratDTO(
            sigle='FOOBAR',
            intitule='Foobar',
            annee=2021,
            sigle_entite_gestion="CDE",
            campus="Mons",
            type=TrainingType.PHD.name,
            campus_inscription='Mons',
            code='FOOBAR',
        )
        self.assertEqual(
            format_training(formation),
            'Foobar (Mons) <span class="training-acronym">FOOBAR</span>',
        )

    def test_format_scholarship_with_long_name_and_short_name(self):
        scholarship = Scholarship(
            short_name='ERASMUS-1',
            long_name='-- ERASMUS-1 --',
            type=TypeBourse.ERASMUS_MUNDUS.name,
        )
        self.assertEqual(format_scholarship(scholarship), '-- ERASMUS-1 --')

    def test_format_scholarship_without_long_name(self):
        scholarship = Scholarship(short_name='ERASMUS-1', long_name='', type=TypeBourse.ERASMUS_MUNDUS.name)
        self.assertEqual(format_scholarship(scholarship), 'ERASMUS-1')

    def test_split_training_id(self):
        training_id = 'INFO1-2020'
        self.assertEqual(
            split_training_id(training_id),
            (
                'INFO1',
                '2020',
            ),
        )

        training_id = 'INF-1234-2020'
        self.assertEqual(
            split_training_id(training_id),
            (
                'INF-1234',
                '2020',
            ),
        )

        training_id = 'INFO1-0'
        self.assertEqual(split_training_id(training_id), tuple())

    def test_get_training_id(self):
        training = {'sigle': 'INFO1', 'annee': 2020}
        self.assertEqual(get_training_id(training), 'INFO1-2020')

    def test_get_uuid_returns_uuid_if_value_if_uuid(self):
        uuid_value = uuid.uuid4()
        self.assertEqual(get_uuid_value(str(uuid_value)), uuid_value)

    def test_get_uuid_returns_input_value_if_not_uuid(self):
        other_value = 'abcdef'
        self.assertEqual(get_uuid_value(other_value), other_value)

    def test_format_academic_year_with_empty_string(self):
        """Check that the format_academic_year returns an empty string if the input is empty."""
        self.assertEqual(format_academic_year(''), '')

    def test_format_academic_year_with_string_year(self):
        """Check that the format_academic_year returns a valid string if the input is a string."""
        self.assertEqual(format_academic_year('2018'), '2018-2019')

    def test_format_academic_year_with_int_year(self):
        """Check that the format_academic_year returns a valid string if the input is an integer."""
        self.assertEqual(format_academic_year(2018), '2018-2019')
