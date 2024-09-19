# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from dal import forward
from django import forms
from django.utils.translation import gettext_lazy as _, pgettext_lazy as __

from admission.constants import BE_ISO_CODE, FIELD_REQUIRED_MESSAGE
from admission.contrib.forms import (
    get_country_initial_choices,
    get_example_text,
    PhoneField,
    autocomplete,
)
from admission.utils import force_title


class DoctorateAdmissionCoordonneesForm(forms.Form):
    show_contact = forms.BooleanField(
        required=False,
        label=_("I would like to receive my mail at an address other than my legal address"),
    )
    private_email = forms.EmailField(
        label=__("admission", "Personal email"),
        required=False,
    )
    phone_mobile = PhoneField(
        label=__('admission', "Telephone (mobile)"),
        max_length=30,
    )
    emergency_contact_phone = PhoneField(
        required=False,
        label=_("Emergency contact (telephone number)"),
        max_length=30,
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'admission/formatter.js',
            'jquery.mask.min.js',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tick the show contact checkbox only if there is data in contact
        self.fields["show_contact"].initial = self.initial['contact'] is not None

        # Some fields are disabled only if they are not already set
        if self.initial.get('private_email'):
            self.fields['private_email'].disabled = True


class DoctorateAdmissionAddressForm(forms.Form):
    street = forms.CharField(
        required=False,
        label=_("Street"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Rue des ponts'),
            },
        ),
        max_length=255,
    )
    street_number = forms.CharField(
        required=False,
        label=__("address", "Number"),
        max_length=20,
    )
    postal_box = forms.CharField(
        required=False,
        label=_("Box"),
        max_length=20,
    )
    postal_code = forms.CharField(
        required=False,
        label=_("Postcode"),
        max_length=20,
    )
    city = forms.CharField(
        required=False,
        label=_("City"),
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('Louvain-la-Neuve'),
            },
        ),
        max_length=255,
    )
    country = forms.CharField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:country",
            attrs={
                "data-html": True,
            },
        ),
    )
    # Enable autocompletion only for Belgium postal codes
    be_postal_code = forms.CharField(
        required=False,
        label=_("Postcode"),
        max_length=20,
    )
    be_city = forms.CharField(
        required=False,
        label=_("City"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:city",
            forward=(forward.Field('be_postal_code', 'postal_code'),),
        ),
        max_length=255,
    )

    def __init__(self, person=None, check_coordinates_fields=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_coordinates_fields = check_coordinates_fields
        self.fields['country'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("country"), self.initial.get("country")),
            person,
        )
        if self.data.get(self.add_prefix('country'), self.initial.get('country')) == BE_ISO_CODE:
            self.initial["be_postal_code"] = self.initial.get("postal_code")
            self.initial["be_city"] = self.initial.get("city")
            initial_choice_needed = self.data.get(self.add_prefix('be_city'), self.initial.get("be_city"))
            if initial_choice_needed:
                self.fields['be_city'].widget.choices = [(initial_choice_needed, initial_choice_needed)]

    def clean(self):
        cleaned_data = super().clean()

        mandatory_address_fields = [
            "street_number",
            "country",
            "street",
        ]

        # Either one of following data couple is mandatory :
        # (postal_code / city) or (be_postal_code / be_city)
        if cleaned_data.get("country") == BE_ISO_CODE:
            mandatory_address_fields.extend(["be_postal_code", "be_city"])
        else:
            mandatory_address_fields.extend(["postal_code", "city"])

        if self.check_coordinates_fields:
            for field in mandatory_address_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)

        # Lowercase the specified fields
        for field in ['street', 'city']:
            if cleaned_data.get(field):
                cleaned_data[field] = force_title(cleaned_data[field])

        return cleaned_data
