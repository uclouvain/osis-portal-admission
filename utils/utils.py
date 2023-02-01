import re
import uuid
from typing import Union

from osis_admission_sdk.model.doctorat_dto import DoctoratDTO
from osis_admission_sdk.model.scholarship import Scholarship

from osis_admission_sdk.model.formation_continue_dto import FormationContinueDTO

from osis_admission_sdk.model.formation_generale_dto import FormationGeneraleDTO

from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.address import Address
from osis_reference_sdk.model.high_school import HighSchool


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


def format_high_school_title(high_school: HighSchool):
    """Return the concatenation of the high school name and city."""
    return '{} <span class="high-school-address">{}, {}</span>'.format(
        high_school['name'],
        ' '.join([high_school['street'], high_school['street_number']]),
        ' '.join([high_school['zipcode'], high_school['city']]),
    )


def format_training(training: Union[DoctoratDTO, FormationContinueDTO, FormationGeneraleDTO]):
    return '{intitule} ({campus}) - {sigle}'.format_map(training)


def format_training_with_year(training: Union[DoctoratDTO, FormationContinueDTO, FormationGeneraleDTO]):
    return '{annee} - {intitule} ({campus}) - {sigle}'.format_map(training)


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
