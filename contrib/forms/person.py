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
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.enums.person import GENDER_CHOICES, SEX_CHOICES
from admission.services.autocomplete import AdmissionAutocompleteService
from base.models.academic_year import AcademicYear
from osis_document.contrib.forms import FileUploadField


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

        countries = [('', '')] + [(
            result.pk,
            result.name if get_language() == settings.LANGUAGE_CODE else result.name_en,
        ) for result in AdmissionAutocompleteService().autocomplete_countries()]
        self.fields['birth_country'].widget.choices = countries
        self.fields['country_of_citizenship'].widget.choices = countries


class DoctorateAdmissionCoordonneesForm(forms.Form):
    residential_street = forms.CharField(required=False, label=_("Street"))
    residential_street_number = forms.CharField(
        required=False,
        label=_("Street number"),
    )
    residential_box = forms.CharField(required=False, label=_("Box"))
    residential_location = forms.CharField(required=False, label=_("Location"))
    residential_postal_code = forms.CharField(required=False, label=_("Postal code"))
    residential_city = forms.CharField(required=False, label=_("City"))
    residential_country = forms.IntegerField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2,
    )

    show_contact = forms.BooleanField(
        required=False,
        label=_("Is your contact address different from your residential address?"),
    )

    contact_street = forms.CharField(required=False, label=_("Street"))
    contact_street_number = forms.CharField(required=False, label=_("Street number"))
    contact_box = forms.CharField(required=False, label=_("Box"))
    contact_location = forms.CharField(required=False, label=_("Location"))
    contact_postal_code = forms.CharField(required=False, label=_("Postal code"))
    contact_city = forms.CharField(required=False, label=_("City"))
    contact_country = forms.IntegerField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2,
    )

    email = forms.EmailField(disabled=True, label=_("Email"))
    phone_mobile = forms.CharField(required=False, label=_("Mobile phone"))

    class Media:
        js = ('dependsOn.min.js',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        countries = [('', '')] + [(
            result.pk,
            result.name if get_language() == settings.LANGUAGE_CODE else result.name_en,
        ) for result in AdmissionAutocompleteService().autocomplete_countries()]
        self.fields['residential_country'].widget.choices = countries
        self.fields['contact_country'].widget.choices = countries

        # Tick the show contact checkbox only if there is data with "contact_" prefix
        if any(v for k, v in self.initial.items() if k.startswith("contact_")):
            self.fields["show_contact"].initial = True

    def clean(self):
        cleaned_data = super().clean()
        validation_errors = []

        contact_street = cleaned_data.get("contact_street", None)
        contact_box = cleaned_data.get("contact_box", None)

        if not any([contact_box, contact_street]):
            error_message = _("please set either contact_street or contact_box")
            self.add_error('contact_box', error_message)
            self.add_error('contact_street', error_message)

        contact_street_number = cleaned_data.get("contact_street_number", None)
        contact_location = cleaned_data.get("contact_location", None)
        contact_postal_code = cleaned_data.get("contact_postal_code", None)
        contact_city = cleaned_data.get("contact_city", None)
        contact_country = cleaned_data.get("contact_country", None)

        contact_address_fields = [
            contact_street_number,
            contact_location,
            contact_postal_code,
            contact_city,
            contact_country,
        ]
        if any(contact_address_fields) and not all(contact_address_fields):
            validation_errors.append(ValidationError("Please fill all the contact address fields"))

        residential_box = cleaned_data.get("residential_box", None)
        residential_street = cleaned_data.get("residential_street", None)

        if not any([residential_box, residential_street]):
            error_message = _("please set either residential_street or residential_box")
            self.add_error('residential_box', error_message)
            self.add_error('residential_street', error_message)

        residential_street_number = cleaned_data.get("residential_street_number", None)
        residential_location = cleaned_data.get("residential_location", None)
        residential_postal_code = cleaned_data.get("residential_postal_code", None)
        residential_city = cleaned_data.get("residential_city", None)
        residential_country = cleaned_data.get("residential_country", None)

        residential_address_fields = [
            residential_street_number,
            residential_location,
            residential_postal_code,
            residential_city,
            residential_country,
        ]
        if any(residential_address_fields) and not all(residential_address_fields):
            validation_errors.append(ValidationError("Please fill all the residential address fields"))

        if len(validation_errors) > 0:
            raise ValidationError(validation_errors)

        return cleaned_data


