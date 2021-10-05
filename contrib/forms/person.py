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
