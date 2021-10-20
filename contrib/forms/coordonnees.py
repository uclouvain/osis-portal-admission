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
from dal import autocomplete, forward
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from admission.contrib.forms import get_country_initial_choices


class DoctorateAdmissionCoordonneesForm(forms.Form):
    show_contact = forms.BooleanField(
        required=False,
        label=_("Is your contact address different from your residential address?"),
    )

    email = forms.EmailField(disabled=True, label=_("Email"))
    phone_mobile = forms.CharField(required=False, label=_("Mobile phone"))

    class Media:
        js = ('dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tick the show contact checkbox only if there is data in contact
        if any(self.initial['contact'][k] for k in self.initial['contact'].attribute_map):
            self.fields["show_contact"].initial = True


class DoctorateAdmissionAddressForm(forms.Form):
    street = forms.CharField(required=False, label=_("Street"))
    street_number = forms.CharField(required=False, label=_("Street number"))
    postal_box = forms.CharField(required=False, label=_("Box"))
    location = forms.CharField(required=False, label=_("Location"))
    postal_code = forms.CharField(required=False, label=_("Postal code"))
    city = forms.CharField(required=False, label=_("City"))
    country = forms.CharField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    # Enable autocompletion only for Belgium postal codes
    be_postal_code = forms.CharField(required=False, label=_("Postal code"))
    be_city = forms.CharField(
        required=False,
        label=_("City"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:city",
            forward=(forward.Field('be_postal_code', 'postal_code'),),
        ),
    )
    BE_ISO_CODE = None

    def __init__(self, *args, **kwargs):
        self.BE_ISO_CODE = kwargs.pop("be_iso_code", None)
        super().__init__(*args, **kwargs)
        self.fields['country'].widget.choices = get_country_initial_choices(
            self.initial["country"]
        )
        if self.initial["country"] == self.BE_ISO_CODE:
            self.initial["be_postal_code"] = self.initial["postal_code"]
            self.initial["be_city"] = self.initial["city"]
            initial_choice_needed = self.data.get('be_city', self.initial.get("be_city"))
            if initial_choice_needed:
                self.fields['be_city'].widget.choices = [(initial_choice_needed, initial_choice_needed)]

    def clean(self):
        cleaned_data = super().clean()

        mandatory_address_fields = [
            "street_number",
            "location",
            "country",
        ]

        # Either one of following data couple is mandatory :
        # (postal_code / city) or (be_postal_code / be_city)
        if cleaned_data.get("country") == self.BE_ISO_CODE:
            mandatory_address_fields.extend(["be_postal_code", "be_city"])
        mandatory_address_fields.extend(["postal_code", "city"])

        if any(cleaned_data.get(f) for f in mandatory_address_fields):
            if not all(cleaned_data.get(f) for f in mandatory_address_fields):
                raise ValidationError("Please fill all the address fields")

            street = cleaned_data.get("street")
            postal_box = cleaned_data.get("postal_box")

            if not any([postal_box, street]):
                error_message = _("please set either street or postal_box")
                self.add_error('postal_box', error_message)
                self.add_error('street', error_message)

        return cleaned_data
