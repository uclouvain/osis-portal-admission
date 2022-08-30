import uuid
from typing import Union

from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.address import Address
from osis_reference_sdk.model.high_school import HighSchool


def format_entity_title(entity: Entite):
    """Return the concatenation of the entity name and acronym."""
    return '{title} ({acronym})'.format_map(entity)


def format_entity_address(address: Address):
    """Return the concatenation of the street, street number, postal code, city and state of an address."""
    address_parts = [
        '{street} {street_number}'.format_map(address),
        '{postal_code} {city}'.format_map(address),
        address.state,
    ]
    return ', '.join(filter(lambda part: part and len(part) > 1, address_parts))


def format_high_school_title(high_school: HighSchool):
    """Return the concatenation of the high school name and city."""
    return '{} <span class="high-school-address">{}, {}</span>'.format(
        high_school['name'],
        ' '.join([high_school['street'], high_school['street_number']]),
        ' '.join([high_school['zipcode'], high_school['city']]),
    )


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


def get_uuid_value(value: str) -> Union[uuid.UUID, str]:
    try:
        return uuid.UUID(hex=value)
    except ValueError:
        return value
