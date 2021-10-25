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

from django.conf import settings

from admission.services.reference import CountriesService, LanguageService

EMPTY_CHOICE = (('', ' - '),)


def get_country_initial_choices(iso_code, person):
    """Return the unique initial choice for a country when data is either set from initial or from webservice."""
    if not iso_code:
        return EMPTY_CHOICE
    country = CountriesService.get_country(iso_code=iso_code, person=person)
    return EMPTY_CHOICE + (
        (country.iso_code, country.name_en if settings.LANGUAGE_CODE == 'en' else country.name),
    )


def get_language_initial_choices(language, person):
    """Return the unique initial choice for a language when data is either set from initial or from webservice."""
    if not language:
        return EMPTY_CHOICE
    language = LanguageService.get_language(language=language, person=person)
    return EMPTY_CHOICE + (
        (language.language, language.name_en if settings.LANGUAGE_CODE == 'en' else language.name),
    )
