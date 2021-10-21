from django.conf import settings

from admission.services.reference import CountriesService

EMPTY_CHOICE = (('', ' - '),)


def get_country_initial_choices(iso_code):
    if not iso_code:
        return EMPTY_CHOICE
    country = CountriesService.get_country(iso_code=iso_code)
    return EMPTY_CHOICE + (
        (country.iso_code, country.name_en if settings.LANGUAGE_CODE == 'en' else country.name),
    )
