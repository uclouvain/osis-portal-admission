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
from dal import autocomplete
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.person import GENDER_CHOICES, SEX_CHOICES
from admission.contrib.forms import EMPTY_CHOICE, get_country_initial_choices
from admission.services.reference import AcademicYearService
from osis_document.contrib.forms import FileUploadField

YES = '1'
NO = '0'


class DoctorateAdmissionPersonForm(forms.Form):
    first_name = forms.CharField(
        required=False,
        label=_("First name"),
        help_text=_("(e.g.: Frédéric) <del>frederic FREDERIC</del>)"),
    )
    middle_name = forms.CharField(
        required=False,
        label=_("Other names"),
        help_text=_("(e.g.: Pierre, Paul, Jacques) <del>pierre, paul, JACQUES)</del>"),
    )
    last_name = forms.CharField(
        required=False,
        label=_("Last name"),
        help_text=_("(e.g.: Van der Elst / Vanderelst) <del>VANDERELST</del>)"),
    )
    first_name_in_use = forms.CharField(required=False, label=_("First name in use"))
    sex = forms.ChoiceField(
        required=False,
        label=_("Sex"),
        choices=EMPTY_CHOICE + SEX_CHOICES,
    )
    gender = forms.ChoiceField(
        required=False,
        label=_("Gender"),
        choices=EMPTY_CHOICE + GENDER_CHOICES,
    )

    birth_date = forms.DateField(
        required=False,
        label=_("Birth date"),
        widget=forms.DateInput(attrs={'placeholder': "dd/mm/yyyy"}),
    )
    birth_year = forms.IntegerField(
        required=False,
        label=_("Birth year"),
        widget=forms.NumberInput(attrs={'placeholder': "yyyy"}),
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
        label=_("ID card"),
        max_files=2,
        min_files=0,
    )

    passport = FileUploadField(required=False, label=_("Passport"))

    national_number = forms.CharField(
        required=False,
        label=_("National registry number"),
        help_text=_("Only to provide if you are in possession of a Belgian document of identity. If "
                    "you are of Belgian nationality and you live in Belgium this field is mandatory "
                    "(11 digits length without space, hyphen or dot (Ex:79682312345))."),
    )
    id_card_number = forms.CharField(required=False, label=_("Identity card number"))
    passport_number = forms.CharField(required=False, label=_("Passport number"))
    passport_expiration_date = forms.DateField(
        required=False,
        label=_("Passport expiration date"),
        widget=forms.DateInput(attrs={'placeholder': "dd/mm/yyyy"}),
    )
    id_photo = FileUploadField(required=False, label=_("ID photo"))

    last_registration_year = forms.ChoiceField(required=False, label=_("Last registration year"))

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
        if self.initial.get('last_registration_year'):
            self.initial['already_registered'] = YES

        self.fields['birth_country'].widget.choices = get_country_initial_choices(
            self.initial.get('birth_country'),
            person
        )
        self.fields['country_of_citizenship'].widget.choices = get_country_initial_choices(
            self.initial.get('country_of_citizenship'),
            person
        )
