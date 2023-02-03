# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from dal import autocomplete
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.actor import ActorType
from admission.contrib.enums.supervision import DecisionApprovalEnum
from admission.contrib.forms import (
    AdmissionFileUploadField as FileUploadField,
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_thesis_institute_initial_choices,
)

EXTERNAL_FIELDS = [
    'prenom',
    'nom',
    'email',
    'institution',
    'ville',
    'pays',
    'langue',
]


class DoctorateAdmissionSupervisionForm(forms.Form):
    type = forms.ChoiceField(
        label="",
        choices=ActorType.choices(),
        widget=forms.RadioSelect(),
    )
    tutor = forms.CharField(
        label=_("Search a tutor by name"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:tutor"),
        required=False,
    )
    person = forms.CharField(
        label=_("Search a person by name"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:person"),
        required=False,
    )

    prenom = forms.CharField(
        label=_("First name"),
        required=False,
    )
    nom = forms.CharField(
        label=_("Last name"),
        required=False,
    )
    email = forms.EmailField(
        label=_("Email"),
        required=False,
    )
    est_docteur = forms.BooleanField(
        label=_("Holder of a doctorate with thesis"),
        required=False,
    )
    institution = forms.CharField(
        label=_("Institute"),
        required=False,
    )
    ville = forms.CharField(
        label=_("City"),
        required=False,
    )
    pays = forms.CharField(
        label=_("Country"),
        required=False,
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    langue = forms.ChoiceField(
        label=_("Contact language"),
        required=False,
        choices=EMPTY_CHOICE + tuple(settings.LANGUAGES),
    )

    def __init__(self, person, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pays'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("pays"), self.initial.get("pays")),
            person,
        )

    def clean(self):
        data = super().clean()
        some_external_fields_filled = any(data.get(field) for field in EXTERNAL_FIELDS)
        all_external_fields_filled = all(data.get(field) for field in EXTERNAL_FIELDS)
        if (
            data.get('type') == ActorType.CA_MEMBER.name
            and not some_external_fields_filled
            and not data.get('person')
            or data.get('type') == ActorType.PROMOTER.name
            and not some_external_fields_filled
            and not data.get('tutor')
        ):
            self.add_error(None, _("You must reference a person in UCLouvain or create an external one."))
        elif data.get('type') == ActorType.PROMOTER.name and some_external_fields_filled and data.get('tutor'):
            self.add_error('tutor', _("A person cannot be referenced at the same time an external person is filled."))
        elif data.get('type') == ActorType.CA_MEMBER.name and some_external_fields_filled and data.get('person'):
            self.add_error('person', _("A person cannot be referenced at the same time an external person is filled."))
        elif some_external_fields_filled and not all_external_fields_filled:
            for field in EXTERNAL_FIELDS:
                if not data.get(field):
                    self.add_error(field, _("This field is required."))
        return data

    class Media:
        js = (
            'js/dependsOn.min.js',
            # Add osis-document script in case of approved-by-pdf documents
            'osis_document/osis-document.umd.min.js',
        )
        css = {'all': ('osis_document/osis-document.css',)}


class DoctorateAdmissionApprovalForm(forms.Form):
    decision = forms.ChoiceField(
        label=_("Decision"),
        choices=DecisionApprovalEnum.choices(),
        widget=forms.RadioSelect,
        required=True,
    )
    motif_refus = forms.CharField(
        label=_('Rejection reason'),
        required=False,
        max_length=50,
    )
    commentaire_interne = forms.CharField(
        label=_('Internal comment'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 5,
            },
        ),
        help_text=_("This comment will only be visible to the administrators."),
    )
    commentaire_externe = forms.CharField(
        label=_('Comment for the candidate'),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 5,
            },
        ),
        help_text=_("This comment will be visible to all users who have access to this page."),
    )
    institut_these = forms.CharField(
        label=_("Research institute"),
        required=False,
        widget=autocomplete.ListSelect2(
            url="admission:autocomplete:institute",
            attrs={
                'data-minimum-input-length': 3,
            },
        ),
    )

    def __init__(self, *args, include_institut_these=False, person=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not include_institut_these:
            del self.fields['institut_these']
        else:
            # Add the specified institute in the choices of the related field
            self.fields['institut_these'].widget.choices = get_thesis_institute_initial_choices(
                self.data.get(self.add_prefix("institut_these"), self.initial.get("institut_these")),
                person,
            )

    def clean(self):
        data = super().clean()
        if data.get('decision') == DecisionApprovalEnum.DECLINED.name and not data.get('motif_refus'):
            self.add_error('motif_refus', _("This field is required."))
        if (
            data.get('decision') == DecisionApprovalEnum.APPROVED.name
            and 'institut_these' in self.fields
            and not data.get('institut_these')
        ):
            self.add_error('institut_these', _("This field is required."))

    class Media:
        js = ('js/dependsOn.min.js',)


class DoctorateAdmissionApprovalByPdfForm(forms.Form):
    uuid_membre = forms.CharField(
        widget=forms.HiddenInput,
        required=True,
    )
    pdf = FileUploadField(
        label=_("PDF file"),
        required=True,
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
    )
