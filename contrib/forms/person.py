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
from functools import lru_cache

from dal import autocomplete, forward
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import get_language, gettext_lazy as _
from osis_document.contrib.forms import FileUploadField

from admission.contrib.enums.person import GENDER_CHOICES, SEX_CHOICES
from admission.services.autocomplete import AdmissionAutocompleteService
from base.models.academic_year import AcademicYear


@lru_cache
def get_countries_choices():
    return [('', '')] + [(
        result.pk,
        result.name if get_language() == settings.LANGUAGE_CODE else result.name_en,
    ) for result in AdmissionAutocompleteService().autocomplete_countries()]


class DoctorateAdmissionPersonForm(forms.Form):
    first_name = forms.CharField(required=False, label=_("First name"))
    middle_name = forms.CharField(required=False, label=_("Other names"))
    last_name = forms.CharField(required=False, label=_("Last name"))
    first_name_in_use = forms.CharField(required=False, label=_("First name in use"))
    sex = forms.ChoiceField(
        required=False,
        label=_("Sex"),
        choices=(('', ' - '),) + SEX_CHOICES,
    )
    gender = forms.ChoiceField(
        required=False,
        label=_("Gender"),
        choices=(('', ' - '),) + GENDER_CHOICES,
    )

    birth_date = forms.DateField(required=False, label=_("Birth date"))
    birth_year = forms.IntegerField(required=False, label=_("Birth year"))
    birth_country = forms.CharField(
        required=False,
        label=_("Birth country"),
        widget=autocomplete.ListSelect2,
    )
    birth_place = forms.CharField(required=False, label=_("Birth place"))
    country_of_citizenship = forms.CharField(
        required=False,
        label=_("Country of citizenship"),
        widget=autocomplete.ListSelect2,
    )

    language = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=settings.LANGUAGES,
    )
    id_card = FileUploadField(required=False, label=_("ID card"))

    passport = FileUploadField(required=False, label=_("Passport"))

    national_number = forms.CharField(required=False, label=_("National number"))
    id_card_number = forms.CharField(required=False, label=_("ID card number"))
    passport_number = forms.CharField(required=False, label=_("Passport number"))
    passport_expiration_date = forms.DateField(required=False, label=_("Passport expiration date"))
    id_photo = FileUploadField(required=False, label=_("ID photo"))

    last_registration_year = forms.ChoiceField(required=False, label=_("Last registration year"))

    unknown_birth_date = forms.BooleanField(required=False, label=_("Unknown birth date"))
    already_registered = forms.BooleanField(
        required=False,
        widget=forms.RadioSelect(choices=[
            ('0', _("No")),
            ('1', _("Yes")),
        ]),
        label="",
    )

    class Media:
        js = ('dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['last_registration_year'].choices = [('', '')]
        for academic_year in AcademicYear.objects.order_by('-year').filter(end_date__year__lte=now().year):
            self.fields['last_registration_year'].choices.append((academic_year.pk, academic_year))
        if self.initial.get('last_registration_year', None):
            self.initial['already_registered'] = '1'

        self.fields['birth_country'].widget.choices = get_countries_choices()
        self.fields['country_of_citizenship'].widget.choices = get_countries_choices()


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
    country = forms.IntegerField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2,
    )
    # autocompletion enable only for Belgium postal codes
    be_postal_code = forms.CharField(required=False, label=_("Postal code"))
    be_city = forms.CharField(
        required=False,
        label=_("City"),
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:city",
            forward=(forward.Field('be_postal_code', 'postal_code'),),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].widget.choices = get_countries_choices()
        if self.initial["country"] == 88:
            self.initial["be_postal_code"] = self.initial["postal_code"]
            self.initial["be_city"] = self.initial["city"]
            self.fields['be_city'].widget.choices = [('', '')] + [
                (city.name, city.name)
                for city
                in AdmissionAutocompleteService().autocomplete_zip_codes(self.initial["postal_code"])
            ]

    def clean(self):
        cleaned_data = super().clean()

        mandatory_address_fields = [
            "street_number",
            "location",
            # "postal_code",
            # "city",
            "country",
        ]
        if any(cleaned_data.get(f, None) for f in mandatory_address_fields):
            if not all(cleaned_data.get(f, None) for f in mandatory_address_fields):
                raise ValidationError("Please fill all the address fields")
            else:
                street = cleaned_data.get("street", None)
                postal_box = cleaned_data.get("postal_box", None)

                if not any([postal_box, street]):
                    error_message = _("please set either street or postal_box")
                    self.add_error('postal_box', error_message)
                    self.add_error('street', error_message)

        return cleaned_data
