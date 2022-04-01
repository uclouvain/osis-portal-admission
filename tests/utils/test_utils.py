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

from django.test import TestCase
from osis_organisation_sdk.model.address import Address
from osis_organisation_sdk.model.entite import Entite

from admission.utils import format_entity_address, format_entity_title


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
