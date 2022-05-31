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
import datetime

from dal import autocomplete
from django import forms
from django.conf import settings
from django.core import validators
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.person import CivilState, GenderEnum, SexEnum
from admission.contrib.forms import (
    CustomDateInput,
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_example_text,
    get_past_academic_years_choices,
)
from osis_document.contrib.forms import FileUploadField

from admission.utils import force_title

YES = '1'
NO = '0'


class DoctorateAdmissionPersonForm(forms.Form):
    first_name = forms.CharField(
        required=False,
        label=_("First name"),
        help_text=get_example_text('Frédéric <del>frederic FREDERIC</del>'),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Frédéric'),
            },
        ),
    )
    middle_name = forms.CharField(
        required=False,
        label=_("Other names"),
        help_text=get_example_text('Pierre, Paul, Jacques <del>pierre, paul, JACQUES)</del>'),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Pierre, Paul, Jacques"),
            },
        ),
    )
    last_name = forms.CharField(
        required=False,
        label=_("Last name"),
        help_text=get_example_text('Van der Elst / Vanderelst <del>VANDERELST</del>'),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Van der Elst / Vanderelst"),
            },
        ),
    )
    first_name_in_use = forms.CharField(
        required=False,
        label=_("First name in use"),
        help_text=get_example_text('Martin <del>martin MARTIN</del>'),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Martin"),
            },
        ),
    )
    sex = forms.ChoiceField(
        label=_("Sex"),
        choices=EMPTY_CHOICE + SexEnum.choices(),
    )
    gender = forms.ChoiceField(
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
        min_value=1900,
        max_value=lambda: datetime.date.today().year,
    )
    civil_state = forms.ChoiceField(
        label=_("Civil status"),
        choices=EMPTY_CHOICE + CivilState.choices(),
    )

    birth_country = forms.CharField(
        label=_("Birth country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    birth_place = forms.CharField(
        label=_("Birth place"),
        help_text=get_example_text("Louvain-la-Neuve <del>louvain-la-neuve</del> <del>LOUVAIN-LA-NEUVE</del>"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Louvain-la-Neuve'),
            },
        ),
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
        label=_("Belgian national registry number (SSIN)"),
        help_text=_(
            "Only to provide if you are in possession of a Belgian document of identity. If "
            "you are of Belgian nationality and you live in Belgium this field is mandatory."
        ),
        validators=[
            validators.RegexValidator(
                r'^(\d{2}[.-]?\d{2}[.-]?\d{2}[.-]?\d{3}[.-]?\d{2})$',
                message=_("The Belgian national register number must consist of 11 digits."),
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "data-mask": "00.00.00-000.00",
                "placeholder": get_example_text("85.07.30-001.33"),
            },
        ),
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
        widget=forms.RadioSelect(
            choices=[
                (NO, _("No")),
                (YES, _("Yes")),
            ],
        ),
        label="",
    )
    last_registration_id = forms.CharField(
        required=False,
        label=_('What was your NOMA (registration id)?'),
        widget=forms.TextInput(
            attrs={
                "data-mask": "00000000",
                "placeholder": get_example_text("10581300"),
            },
        ),
        validators=[
            validators.RegexValidator(r'^[0-9]{8}$', _('The NOMA must contain 8 digits.')),
        ],
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'jquery.mask.min.js',
        )

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_registration_year'].choices = get_past_academic_years_choices(person)
        self.initial['already_registered'] = YES if self.initial.get('last_registration_year') else NO

        if self.initial.get('birth_year'):
            self.initial['unknown_birth_date'] = True

        self.fields['birth_country'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("birth_country"), self.initial.get("birth_country")),
            person,
        )
        self.fields['country_of_citizenship'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("country_of_citizenship"), self.initial.get("country_of_citizenship")),
            person,
        )

    def clean(self):
        data = super().clean()

        # Check the fields which are required if others are specified
        if data.get('unknown_birth_date') and not data.get('birth_year'):
            self.add_error('birth_year', _("This field is required."))

        if data.get('already_registered'):
            if not data.get('last_registration_year'):
                self.add_error('last_registration_year', _("This field is required."))
            if not data.get('last_registration_id'):
                self.add_error('last_registration_id', _("This field is required."))

        if data.get('country_of_citizenship') == 'BE' and not data.get('national_number'):
            self.add_error('national_number', _("This field is required."))

        if not data.get('first_name') and not data.get('last_name'):
            self.add_error('first_name', _('This field is required if the last name is missing.'))
            self.add_error('last_name', _('This field is required if the first name is missing.'))

        if not data.get('id_card') and (data.get('id_card_number') or data.get('national_number')):
            self.add_error('id_card', _("This field is required."))

        if data.get('passport_number'):
            if not data.get('passport_expiration_date'):
                self.add_error('passport_expiration_date', _("This field is required."))
            if not data.get('passport'):
                self.add_error('passport', _("This field is required."))

        # Lowercase the specified names
        for field in ['first_name', 'last_name', 'middle_name', 'first_name_in_use']:
            if data.get(field):
                data[field] = force_title(data[field])

        return data
