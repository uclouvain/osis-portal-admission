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
from functools import partial

from dal import autocomplete
from django import forms
from django.conf import settings
from django.core import validators
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.person import GenderEnum, SexEnum
from admission.contrib.forms import EMPTY_CHOICE, get_country_initial_choices
from admission.services.reference import AcademicYearService
from osis_document.contrib.forms import FileUploadField

YES = '1'
NO = '0'

CustomDateInput = partial(
    forms.DateInput,
    attrs={'placeholder': _("dd/mm/yyyy")},
    format='%d/%m/%Y',
)


class DoctorateAdmissionPersonForm(forms.Form):
    first_name = forms.CharField(
        label=_("First name"),
        help_text=_("(e.g.: Frédéric) <del>frederic FREDERIC</del>)"),
    )
    middle_name = forms.CharField(
        required=False,
        label=_("Other names"),
        help_text=_("(e.g.: Pierre, Paul, Jacques) <del>pierre, paul, JACQUES)</del>"),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        help_text=_("(e.g.: Van der Elst / Vanderelst) <del>VANDERELST</del>)"),
    )
    first_name_in_use = forms.CharField(required=False, label=_("First name in use"))
    sex = forms.ChoiceField(
        required=False,
        label=_("Sex"),
        choices=EMPTY_CHOICE + SexEnum.choices(),
    )
    gender = forms.ChoiceField(
        required=False,
        label=_("Gender"),
        choices=EMPTY_CHOICE + GenderEnum.choices(),
    )

    birth_date = forms.DateField(
        required=False,
        label=_("Birth date"),
        widget=CustomDateInput(),
    )
    birth_year = forms.IntegerField(
        required=False,
        label=_("Birth year"),
        widget=forms.NumberInput(attrs={'placeholder': _("yyyy")}),
        min_value=1000,
        max_value=2999,
    )
    birth_country = forms.CharField(
        required=False,
        label=_("Birth country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    birth_place = forms.CharField(
        required=False,
        label=_("Birth place"),
        help_text=_("(e.g.: Louvain-la-Neuve) <del>louvain-la-neuve</del>)"),
    )
    country_of_citizenship = forms.CharField(
        required=False,
        label=_("Country of citizenship"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )

    language = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=settings.LANGUAGES,
    )
    id_card = FileUploadField(
        required=False,
        label=_("Identity card (both sides)"),
        max_files=2,
    )

    passport = FileUploadField(required=False, label=_("Passport"), max_files=2)

    national_number = forms.CharField(
        required=False,
        label=_("National registry number"),
        help_text=_("Only to provide if you are in possession of a Belgian document of identity. If "
                    "you are of Belgian nationality and you live in Belgium this field is mandatory "
                    "(11 digits length without space, hyphen or dot (Ex:79682312345))."),
        validators=[validators.RegexValidator(r'\d{11}')],
    )
    id_card_number = forms.CharField(required=False, label=_("Identity card number"))
    passport_number = forms.CharField(required=False, label=_("Passport number"))
    passport_expiration_date = forms.DateField(
        required=False,
        label=_("Passport expiration date"),
        widget=CustomDateInput(),
    )
    id_photo = FileUploadField(required=False, label=_("Identity picture"), max_files=1)

    last_registration_year = forms.ChoiceField(
        required=False,
        label=_("What was your last year of UCLouvain enrollment?"),
    )

    unknown_birth_date = forms.BooleanField(required=False, label=_("Unknown birth date"))
    already_registered = forms.BooleanField(
        required=False,
        widget=forms.RadioSelect(choices=[
            (NO, _("No")),
            (YES, _("Yes")),
        ]),
        label="",
    )

    class Media:
        js = ('dependsOn.min.js',)

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        year_choices = tuple(
            (academic_year.year, "{}-{}".format(academic_year.year, str(academic_year.year + 1)[2:]))
            for academic_year in AcademicYearService.get_academic_years(person)
        )
        self.fields['last_registration_year'].choices = EMPTY_CHOICE + year_choices
        self.initial['already_registered'] = YES if self.initial.get('last_registration_year') else NO

        if self.initial.get('birth_year'):
            self.initial['unknown_birth_date'] = True

        self.fields['birth_country'].widget.choices = get_country_initial_choices(
            self.initial.get('birth_country'),
            person
        )
        self.fields['country_of_citizenship'].widget.choices = get_country_initial_choices(
            self.initial.get('country_of_citizenship'),
            person
        )

    def clean(self):
        data = super().clean()
        if data.get('unknown_birth_date') and not data.get('birth_year'):
            self.add_error('birth_year', _("This field is required."))
        if data.get('already_registered') and not data.get('last_registration_year'):
            self.add_error('last_registration_year', _("This field is required."))
        if data.get('passport_number') and not data.get('passport_expiration_date'):
            self.add_error('passport_expiration_date', _("This field is required."))
        elif data.get('passport_expiration_date') and not data.get('passport_number'):
            self.add_error('passport_number', _("This field is required."))
        return data
