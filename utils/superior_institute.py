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
from base.models.entity_version import EntityVersion


def format_address(street='', street_number='', postal_code='', city='', country=''):
    """Return the concatenation of the specified street, street number, postal code, city and country."""
    address_parts = [
        f'{street} {street_number}',
        f'{postal_code} {city}',
        country,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_school_title(school):
    """Return the concatenation of the school name and city."""
    address = format_address(
        street=school.street,
        street_number=school.street_number,
        postal_code=school.zipcode,
        city=school.city,
    )
    return f'{school.name} <span class="school-address">{address}</span>'
