from osis_organisation_sdk.model.entite import Entite
from osis_organisation_sdk.model.address import Address


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
