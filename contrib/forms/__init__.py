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
from functools import partial

from django import forms
from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from admission.services.organisation import EntitiesService
from admission.services.reference import CountriesService, LanguageService, AcademicYearService, HighSchoolService
from admission.utils import format_entity_title, format_high_school_title
from base.tests.factories.academic_year import get_current_year

EMPTY_CHOICE = (('', ' - '),)


def get_country_initial_choices(iso_code=None, person=None, loaded_country=None):
    """Return the unique initial choice for a country when data is either set from initial or from webservice."""
    if not iso_code and not loaded_country:
        return EMPTY_CHOICE
    country = loaded_country if loaded_country else CountriesService.get_country(iso_code=iso_code, person=person)
    return EMPTY_CHOICE + (
        (country.iso_code, country.name if get_language() == settings.LANGUAGE_CODE else country.name_en),
    )


def get_language_initial_choices(code, person):
    """Return the unique initial choice for a language when data is either set from initial or from webservice."""
    if not code:
        return EMPTY_CHOICE
    language = LanguageService.get_language(code=code, person=person)
    return EMPTY_CHOICE + (
        (language.code, language.name if get_language() == settings.LANGUAGE_CODE else language.name_en),
    )


def get_thesis_institute_initial_choices(uuid, person):
    """Return the unique initial choice for an institute when data is either set from initial or webservice."""
    if not uuid:
        return EMPTY_CHOICE
    institute = EntitiesService.get_ucl_entity(person=person, uuid=uuid)
    return EMPTY_CHOICE + ((institute.uuid, format_entity_title(entity=institute)),)


def get_thesis_location_initial_choices(value):
    """Return the unique initial choice for a thesis location when data is either set from initial or webservice."""
    return EMPTY_CHOICE if not value else EMPTY_CHOICE + ((value, value),)


def get_high_school_initial_choices(uuid, person):
    """Return the unique initial choice for an high school when data is either set from initial or webservice."""
    if not uuid:
        return EMPTY_CHOICE
    high_school = HighSchoolService.get_high_school(person=person, uuid=uuid)
    return EMPTY_CHOICE + ((high_school.uuid, format_high_school_title(high_school=high_school)),)


def get_past_academic_years_choices(person):
    """Return a list of choices of past academic years."""
    current_year = get_current_year()
    lower_year = current_year - 100
    return EMPTY_CHOICE + tuple(
        (academic_year.year, f"{academic_year.year}-{academic_year.year + 1}")
        for academic_year in AcademicYearService.get_academic_years(person)
        if current_year >= academic_year.year >= lower_year
    )


class CustomDateInput(forms.DateInput):
    def __init__(self, attrs=None, format='%d/%m/%Y'):
        if attrs is None:
            attrs = {
                'placeholder': _("dd/mm/yyyy"),
                'data-mask' '': '00/00/0000',
            }
        super().__init__(attrs, format)

    class Media:
        js = ('jquery.mask.min.js',)


def get_example_text(example: str):
    return _("e.g.: %(example)s") % {'example': example}
