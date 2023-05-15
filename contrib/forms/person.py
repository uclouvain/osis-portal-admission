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

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.enums.person import CivilState, GenderEnum, SexEnum, IdentificationType
from admission.contrib.forms import (
    CustomDateInput,
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_example_text,
    get_past_academic_years_choices,
    RadioBooleanField,
    AdmissionFileUploadField as FileUploadField,
    IMAGE_MIME_TYPES,
)
from admission.utils import force_title

YES = '1'
NO = '0'


class DoctorateAdmissionPersonForm(forms.Form):
    # Identification
    first_name = forms.CharField(
        required=False,
        label=_("First name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Maria'),
            },
        ),
    )
    middle_name = forms.CharField(
        required=False,
        label=_("Other first names"),
        help_text=_(
            "Please indicate your other first names in accordance with your identity document. "
            "If no other first name is mentioned on your identity document, you don't need to indicate anything."
        ),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Pierre, Paul, Jacques"),
            },
        ),
    )
    last_name = forms.CharField(
        required=False,
        label=_("Last name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Smith"),
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
    unknown_birth_date = forms.BooleanField(required=False, label=_("Unknown birth date"))
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
        help_text=_('This choice will define the language of communication throughout your admission process.'),
    )

    # Proof of identity
    id_card = FileUploadField(
        required=False,
        label=_("Identity card (both sides)"),
        max_files=2,
    )

    passport = FileUploadField(required=False, label=_("Passport"), max_files=2)

    has_national_number = RadioBooleanField(
        label=_("Have you got a Belgian national registry number (SSIN)?"),
    )
    identification_type = forms.ChoiceField(
        label=_("Please provide one of these two identification information:"),
        required=False,
        choices=IdentificationType.choices(),
        widget=forms.RadioSelect,
    )
    national_number = forms.CharField(
        required=False,
        label=_("Belgian national registry number (SSIN)"),
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
        help_text=_(
            'The Belgian national register number (or NISS, Social Security Identification Number) is a '
            'number composed of 11 digits, the first 6 of which refer to the date of birth of the concerned '
            'person. This number is assigned to every person living in Belgium when they register with '
            'the municipality (or other official body). It can be found on the Belgian identity card or on the '
            'residence permit.'
        ),
    )
    id_card_number = forms.CharField(required=False, label=_("Identity card number"))
    passport_number = forms.CharField(required=False, label=_("Passport number"))
    id_photo = FileUploadField(
        required=False,
        label=_("Identity picture"),
        max_files=1,
        mimetypes=IMAGE_MIME_TYPES,
    )

    # Already registered
    last_registration_year = forms.ChoiceField(
        required=False,
        label=_("What is your last year of UCLouvain enrollment?"),
    )
    already_registered = RadioBooleanField(
        required=False,
        label=_("Have you previously been registered at UCLouvain?"),
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
            'admission/formatter.js',
        )

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['last_registration_year'].choices = get_past_academic_years_choices(person)
        self.initial['already_registered'] = True if self.initial.get('last_registration_year') else False

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

        if self.initial.get('id_card_number'):
            self.initial['identification_type'] = IdentificationType.ID_CARD_NUMBER.name
        elif self.initial.get('passport_number'):
            self.initial['identification_type'] = IdentificationType.PASSPORT_NUMBER.name
        else:
            self.initial['identification_type'] = ''

        if self.initial.get('national_number'):
            self.initial['has_national_number'] = True
        elif self.initial.get('identification_type'):
            self.initial['has_national_number'] = False

    def clean(self):
        data = super().clean()

        # Check the fields which are required if others are specified
        if data.get('unknown_birth_date'):
            if not data.get('birth_year'):
                self.add_error('birth_year', FIELD_REQUIRED_MESSAGE)
        elif not data.get('birth_date'):
            self.add_error('birth_date', FIELD_REQUIRED_MESSAGE)

        if data.get('already_registered'):
            if not data.get('last_registration_year'):
                self.add_error('last_registration_year', FIELD_REQUIRED_MESSAGE)
            if not data.get('last_registration_id'):
                self.add_error('last_registration_id', FIELD_REQUIRED_MESSAGE)

        if not data.get('first_name') and not data.get('last_name'):
            self.add_error('first_name', _('This field is required if the last name is missing.'))
            self.add_error('last_name', _('This field is required if the first name is missing.'))

        if data.get('has_national_number'):
            if not data.get('national_number'):
                self.add_error('national_number', FIELD_REQUIRED_MESSAGE)
        elif data.get('identification_type') == IdentificationType.ID_CARD_NUMBER.name:
            if not data.get('id_card_number'):
                self.add_error('id_card_number', FIELD_REQUIRED_MESSAGE)
        elif data.get('identification_type') == IdentificationType.PASSPORT_NUMBER.name:
            if not data.get('passport_number'):
                self.add_error('passport_number', FIELD_REQUIRED_MESSAGE)
        else:
            self.add_error('identification_type', FIELD_REQUIRED_MESSAGE)

        # Lowercase the specified names
        for field in ['first_name', 'last_name', 'middle_name', 'first_name_in_use', 'birth_place']:
            if data.get(field):
                data[field] = force_title(data[field])

        return data
