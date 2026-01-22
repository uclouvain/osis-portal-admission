# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
import re
import uuid
from typing import Union

from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from osis_admission_sdk.models.doctorat_dto import DoctoratDTO
from osis_admission_sdk.models.formation_continue_dto import FormationContinueDTO
from osis_admission_sdk.models.formation_generale_dto import FormationGeneraleDTO
from osis_organisation_sdk.models.address import Address
from osis_organisation_sdk.models.entite import Entite
from osis_reference_sdk.models.high_school import HighSchool
from osis_reference_sdk.models.scholarship import Scholarship
from osis_reference_sdk.models.superior_non_university import SuperiorNonUniversity
from osis_reference_sdk.models.university import University


def format_entity_title(entity: Entite):
    """Return the concatenation of the entity name and acronym."""
    return '{title} ({acronym})'.format_map(entity)


def format_address(street='', street_number='', postal_code='', city='', country=''):
    """Return the concatenation of the specified street, street number, postal code, city and country."""
    address_parts = [
        f'{street} {street_number}',
        f'{postal_code} {city}',
        country,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_entity_address(address: Address):
    """Return the concatenation of the street, street number, postal code, city and state of an address."""
    return format_address(address.street, address.street_number, address.postal_code, address.city, address.state)


def format_school_title(school: Union[HighSchool, SuperiorNonUniversity, University]):
    """Return the concatenation of the school name and city."""
    return '{} <span class="school-address">{}</span>'.format(
        school['name'],
        format_address(
            street=school['street'],
            street_number=school['street_number'],
            postal_code=school['zipcode'],
            city=school['city'],
        ),
    )


def format_training(training: Union[DoctoratDTO, FormationContinueDTO, FormationGeneraleDTO]):
    return '{intitule} ({campus}) <span class="training-acronym">{sigle}</span>'.format_map(training)


def format_training_with_year(training: Union[DoctoratDTO, FormationContinueDTO, FormationGeneraleDTO]):
    return '{annee} - {intitule} ({campus}) <span class="training-acronym">{sigle}</span>'.format_map(training)


def format_scholarship(scholarship: Scholarship):
    return scholarship['long_name'] or scholarship['short_name']


def force_title(string: str):
    """
    Return a string in which all words are lowercase, except for the first letter of each one, which can written in
    upper or lower case"""
    title_string = list(string.title())

    for index, char in enumerate(title_string):
        if char.isupper() and string[index].islower():
            title_string[index] = string[index]

    return ''.join(title_string)


def to_snake_case(value):
    return ''.join(['_' + i.lower() if i.isupper() else i for i in value]).lstrip('_')


def split_training_id(training_id):
    result = re.match(r"^(.*)-(\d{4})$", training_id)
    return result.groups() if result else tuple()


def get_training_id(training):
    return "{sigle}-{annee}".format(
        sigle=training['sigle'],
        annee=training['annee'],
    )


def get_uuid_value(value: str) -> Union[uuid.UUID, str]:
    try:
        return uuid.UUID(hex=value)
    except ValueError:
        return value


def format_academic_year(year: Union[int, str, float]):
    """Return the academic year related to a specific year."""
    if not year:
        return ''
    if isinstance(year, (str, float)):
        year = int(year)
    return f'{year}-{year + 1}'


PREFIXES_DOMAINES_FORMATIONS_DENT_MED = {'11', '13'}


def is_med_dent_training(training) -> bool:
    return training.code_domaine[:2] in PREFIXES_DOMAINES_FORMATIONS_DENT_MED


def _mark_safe(value, **kwargs):
    """Mark a string as safe and interpolate variables inside if provided."""
    return mark_safe(value % (kwargs or {}))


mark_safe_lazy = lazy(_mark_safe, str)
