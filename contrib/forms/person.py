# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.conf import settings
from django.core import validators
from django.forms import SelectDateWidget
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE, MINIMUM_BIRTH_YEAR
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
    get_year_choices,
    autocomplete,
    LOWERCASE_MONTHS,
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
        max_length=50,
    )
    middle_name = forms.CharField(
        required=False,
        label=_("Other given names"),
        help_text=_(
            "Please indicate your other given names in accordance with your identity document. "
            "If there are no other given names on your identity document, you do not need to enter anything."
        ),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Pierre, Paul, Jacques"),
            },
        ),
        max_length=50,
    )
    last_name = forms.CharField(
        required=False,
        label=_("Surname"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text("Smith"),
            },
        ),
        max_length=50,
    )
    sex = forms.ChoiceField(
        label=_("Sex"),
        choices=EMPTY_CHOICE + SexEnum.choices(),
    )
    gender = forms.ChoiceField(
        label=_("Gender"),
        choices=EMPTY_CHOICE + GenderEnum.choices(),
    )
    unknown_birth_date = forms.BooleanField(required=False, label=_("Unknown date of birth"))
    birth_date = forms.DateField(
        required=False,
        label=_("Date of birth"),
        widget=SelectDateWidget(
            empty_label=[_('Year'), _('Month'), _('Day')],
            months=LOWERCASE_MONTHS,
        ),
    )
    birth_year = forms.TypedChoiceField(
        required=False,
        label=_("Year of birth"),
        coerce=int,
        widget=forms.Select,
    )
    civil_state = forms.ChoiceField(
        label=_("Civil status"),
        choices=EMPTY_CHOICE + CivilState.choices(),
    )

    birth_country = forms.CharField(
        label=_("Country of birth"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:country",
            attrs={
                "data-html": True,
            },
        ),
    )
    birth_place = forms.CharField(
        label=_("Place of birth"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Louvain-la-Neuve'),
            },
        ),
        max_length=255,
    )
    country_of_citizenship = forms.CharField(
        label=_("Country of citizenship"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:country",
            attrs={
                "data-html": True,
            },
        ),
    )

    language = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=settings.LANGUAGES,
        help_text=_(
            'This choice will define the language of communication throughout your admission process.'
            ' This will also change the interface language.'
        ),
    )

    # Proof of identity
    id_card = FileUploadField(
        required=False,
        label=_("Identity card (both sides)"),
        max_files=2,
    )

    passport = FileUploadField(
        required=False,
        label=_("Passport"),
        max_files=2,
    )

    id_card_expiry_date = forms.DateField(
        required=False,
        label=_('Identity card expiry date'),
        widget=CustomDateInput(),
    )

    passport_expiry_date = forms.DateField(
        required=False,
        label=_('Passport expiry date'),
        widget=CustomDateInput(),
    )

    has_national_number = RadioBooleanField(
        label=_("Do you have a Belgian National Register Number (NISS)?"),
        help_text=_(
            'The Belgian national register number (or NISS, Social Security Identification Number) is a '
            'number composed of 11 digits, the first 6 of which refer to the date of birth of the concerned '
            'person. This number is assigned to every person living in Belgium when they register with '
            'the municipality (or other official body). It can be found on the Belgian identity card or on the '
            'residence permit.'
        ),
    )
    identification_type = forms.ChoiceField(
        label=_("Please provide one of these two pieces of identification information:"),
        required=False,
        choices=IdentificationType.choices(),
        widget=forms.RadioSelect,
    )
    national_number = forms.CharField(
        required=False,
        label=_("Belgian national registry number (NISS)"),
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
    id_card_number = forms.CharField(
        required=False,
        label=_("Identity card number"),
        max_length=255,
    )
    passport_number = forms.CharField(
        required=False,
        label=_("Passport number"),
        max_length=255,
    )
    id_photo = FileUploadField(
        required=False,
        label=_("Identification photo"),
        help_text=_(
            "The photo must follow the following rules:"
            "<ul>"
            "  <li>JPEG or PNG file (.jpg, .jpeg ou .png) up to 10MB</li>"
            "  <li>Identity photo format with a <strong>blank background</strong></li>"
            "  <li>Centered on your <strong>bare face</strong></li>"
            "  <li>Recent and <strong>in colour</strong></li>"
            "  <li>Without any filter nor any contour</li>"
            "</ul>"
        ),
        max_files=1,
        mimetypes=IMAGE_MIME_TYPES,
        with_cropping=True,
        cropping_options={'aspectRatio': 0.766},
    )

    # Already registered
    last_registration_year = forms.ChoiceField(
        required=False,
        label=_("What was the most recent year you were enrolled at UCLouvain?"),
    )
    already_registered = RadioBooleanField(
        required=False,
        label=_("Have you previously enrolled at UCLouvain?"),
    )
    last_registration_id = forms.CharField(
        required=False,
        label=_('What was your NOMA (matriculation number)?'),
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
        self.fields['birth_date'].widget.years = range(MINIMUM_BIRTH_YEAR, datetime.date.today().year + 1)
        self.initial['already_registered'] = True if self.initial.get('last_registration_year') else False

        if self.initial.get('birth_year'):
            self.initial['unknown_birth_date'] = True

        self.fields['birth_year'].choices = get_year_choices()

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

        if person and not person.global_id.startswith("8"):
            self._disable_fields_when_internal_account()

    def _disable_fields_when_internal_account(self):
        # Cas: Les informations des comptes internes doivent être modifié via une autre procédure
        fieldname_to_disabled = ['first_name', 'last_name', 'unknown_birth_date', 'birth_date', 'sex', 'birth_country']
        for fieldname in fieldname_to_disabled:
            self.fields[fieldname].disabled = True

        fieldname_to_add_helptext = ['first_name', 'last_name', 'birth_date', 'sex', 'birth_country']
        help_text_modification_internal_account = _(
            "Any modification of personal data must be communicated to the Registration Department by email by "
            "producing a photocopy of both sides of their identity card incorporating this modification."
        )
        for fieldname in fieldname_to_add_helptext:
            self.fields[fieldname].help_text = help_text_modification_internal_account

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

        if not data.get('first_name') and not data.get('last_name'):
            self.add_error('first_name', _('This field is required if the surname is missing.'))
            self.add_error('last_name', _('This field is required if the first name is missing.'))

        if data.get('has_national_number'):
            if not data.get('national_number'):
                self.add_error('national_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('id_card_expiry_date'):
                self.add_error('id_card_expiry_date', FIELD_REQUIRED_MESSAGE)
        elif data.get('identification_type') == IdentificationType.ID_CARD_NUMBER.name:
            if not data.get('id_card_number'):
                self.add_error('id_card_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('id_card_expiry_date'):
                self.add_error('id_card_expiry_date', FIELD_REQUIRED_MESSAGE)
        elif data.get('identification_type') == IdentificationType.PASSPORT_NUMBER.name:
            if not data.get('passport_number'):
                self.add_error('passport_number', FIELD_REQUIRED_MESSAGE)
            if not data.get('passport_expiry_date'):
                self.add_error('passport_expiry_date', FIELD_REQUIRED_MESSAGE)
        else:
            self.add_error('identification_type', FIELD_REQUIRED_MESSAGE)

        # Lowercase the specified names
        for field in ['first_name', 'last_name', 'middle_name', 'birth_place']:
            if data.get(field):
                data[field] = force_title(data[field])

        return data
