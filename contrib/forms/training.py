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
from functools import partial
from typing import List, Optional

from dal import autocomplete
from django import forms
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy

from admission.contrib.enums.training import ChoixComiteSelection, ChoixStatutPublication
from admission.contrib.forms import CustomDateInput
from osis_document.contrib import FileUploadField


class ConfigurableActivityTypeWidget(forms.MultiWidget):
    """Form widget to handle a configurable (from CDDConfiguration) list of choices, or other"""

    template_name = 'admission/doctorate/forms/activity_type_widget.html'
    media = forms.Media(
        js=[
            'js/dependsOn.min.js',
            'admission/configurable_type_widget.js',
        ]
    )

    def __init__(self, *args, **kwargs):
        widgets = {
            '': forms.Select(),
            'other': forms.TextInput(),
        }
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        # No value, no value to both fields
        if not value:
            return [None, None]
        # Pass value to radios if part of choices
        if value in dict(self.widgets[0].choices):
            return [value, '']
        # else pass value to textinput
        return ['other', value]

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        # Remove the required attribute on textinput
        context['widget']['subwidgets'][1]['attrs']['required'] = False
        return context


class ConfigurableActivityTypeField(forms.MultiValueField):
    """Form field to handle a configurable (from CDD) list of choices, or other"""

    widget = ConfigurableActivityTypeWidget

    def __init__(self, source: str = '', choices: Optional[List[str]] = None, **kwargs):
        self.source = source
        self.choices = choices
        fields = [forms.CharField(required=False), forms.CharField(required=False)]
        super().__init__(fields, require_all_fields=False, **kwargs)

    def validate(self, value):
        # We do require all fields, but we want to check the final (compressed value)
        super(forms.MultiValueField, self).validate(value)

    def get_bound_field(self, form, field_name):
        values = self.choices or []
        if self.source:
            # Update radio choices from CDD configuration
            values = form.config_types.get(self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)

    def compress(self, data_list):
        # On save, take the other value if "other" is chosen
        radio, other = data_list or [None, None]
        return radio if radio != "other" else other


IsOnlineField = partial(
    forms.BooleanField,
    label=_("Online or in person"),
    initial=False,
    required=False,
    widget=forms.RadioSelect(choices=((False, _("In person")), (True, _("Online")))),
)


class ActivityFormMixin(forms.Form):
    config_types = {}

    type = ConfigurableActivityTypeField(label=_("Activity type"))
    title = forms.CharField(label=_("Title"), max_length=200)
    participating_proof = FileUploadField(label=_("Participation certification"), max_files=1)
    start_date = forms.DateField(label=_("Begin date"), widget=CustomDateInput())
    end_date = forms.DateField(label=_("End date"), widget=CustomDateInput())
    participating_days = forms.DecimalField(
        label=_("Number of days participating"),
        max_digits=3,
        decimal_places=1,
    )
    is_online = IsOnlineField()
    country = forms.CharField(
        required=False,
        label=_("Country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    city = forms.CharField(label=_("City"), max_length=100)
    organizing_institution = forms.CharField(label=_("Organizing institution"), max_length=100)
    website = forms.URLField(label=_("Website"))
    committee = forms.ChoiceField(
        choices=ChoixComiteSelection.choices(),
    )
    dial_reference = forms.CharField(label=_("Référence DIAL.Pr"), max_length=100)
    acceptation_proof = FileUploadField(label=_("Participation certification"), max_files=1)
    summary = FileUploadField(label=pgettext_lazy("paper summary", "Summary"), max_files=1)
    subtype = forms.CharField(label=_("Activity subtype"), max_length=100)
    subtitle = forms.CharField(widget=forms.Textarea())
    authors = forms.CharField(label=_("Authors"), max_length=100)
    role = forms.CharField(label=_("Role"), max_length=100)
    keywords = forms.CharField(label=_("Keywords"), max_length=100)
    journal = forms.CharField(label=_("Journal"), max_length=100)
    publication_status = forms.ChoiceField(choices=ChoixStatutPublication.choices())
    hour_volume = forms.CharField(max_length=100)
    ects = forms.DecimalField(
        label=_("ECTS credits"),
        max_digits=4,
        decimal_places=2,
    )
    comment = forms.CharField(label=_("Comment"), widget=forms.Textarea())

    def __init__(self, config_types=None, *args, **kwargs) -> None:
        self.config_types = config_types or {}
        super().__init__(*args, **kwargs)
        # Remove unneeded fields
        for field_name in list(self.fields.keys()):
            if field_name not in self.Meta.fields:
                del self.fields[field_name]
        # Make all fields not required and apply label overrides
        for field_name in self.fields:
            # if not isinstance(self.fields[field_name], ConfigurableActivityTypeField):
            if field_name != 'type':
                self.fields[field_name].required = False
            self.fields[field_name].label = self.Meta.labels.get(field_name, self.fields[field_name].label)


class ConferenceForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/conference.html"
    type = ConfigurableActivityTypeField('conference_types', label=_("Type of activity"))

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'start_date',
            'end_date',
            'participating_days',
            'is_online',
            'website',
            'country',
            'city',
            'organizing_institution',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Name of the manifestation"),
            'website': _("Event website"),
            'ects': _("ECTS for participating"),
        }
        help_texts = {
            'title': _("Name in the language of the manifestation"),
        }


class ConferenceCommunicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/conference_communication.html"
    type = ConfigurableActivityTypeField(
        label=_("Type of communication"),
        choices=[
            _("Poster"),
            _("Oral communication"),
        ],
    )

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'summary',
            'committee',
            'acceptation_proof',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'summary': _("Summary of the communication"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Attestation of the communication"),
            'committee': _("Selection committee"),
        }


class ConferencePublicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/conference_publication.html"
    type = ConfigurableActivityTypeField('conference_publication_types', label=_("Type of publication"))

    class Meta:
        fields = [
            'type',
            'ects',
            'title',
            'authors',
            'role',
            'keywords',
            'summary',
            'committee',
            'journal',
            'dial_reference',
            'participating_proof',
            'comment',
        ]
        labels = {
            'type': _("Type of publication"),
            'title': _("Title of the publication"),
            'committee': _("Selection committee"),
            'summary': pgettext_lazy("paper summary", "Summary"),
            'participating_proof': _("Proof of acceptation or publication"),
        }


class CommunicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/communication.html"
    type = ConfigurableActivityTypeField('communication_types', label=_("Type of activity"))
    subtype = ConfigurableActivityTypeField(
        label=_("Type of communication"),
        choices=[
            _("Oral exposé"),
            _("Poster"),
        ],
    )
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200)

    class Meta:
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'subtitle',
            'summary',
            'committee',
            'acceptation_proof',
            'participating_proof',
            'dial_reference',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name of the activity"),
            'start_date': _("Date of the activity"),
            'website': _("Event website"),
            'acceptation_proof': _("Proof of acceptation by the committee"),
            'participating_proof': _("Communication attestation"),
            'committee': _("Selection committee"),
            'summary': _("Summary of the communication"),
        }


class PublicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/publication.html"
    type = ConfigurableActivityTypeField('publication_types', label=_("Type of activity"))

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'authors',
            'role',
            'keywords',
            'summary',
            'journal',
            'publication_status',
            'dial_reference',
            'ects',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the publication"),
            'start_date': _("Date of the publication"),
            'publication_status': _("Publication status"),
            'participating_proof': _("Proof"),
        }


class ResidencyForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/residency.html"
    type = ConfigurableActivityTypeField('residency_types', label=_("Type of activity"))

    class Meta:
        fields = [
            'type',
            'ects',
            'subtitle',
            'start_date',
            'end_date',
            'country',
            'city',
            'participating_proof',
            'comment',
        ]
        labels = {
            'subtitle': _("Description of the activity"),
            'participating_proof': _("Proof (if needed)"),
        }


class ResidencyCommunicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/residency_communication.html"
    type = ConfigurableActivityTypeField("residency_communication_types", label=_("Type of activity"))
    subtype = ConfigurableActivityTypeField('residency_communication_subtypes', label=_("Type of communication"))
    subtitle = forms.CharField(label=_("Title of the communication"), max_length=200)

    class Meta:
        fields = [
            'type',
            'subtype',
            'title',
            'start_date',
            'is_online',
            'organizing_institution',
            'website',
            'subtitle',
            'ects',
            'summary',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Name of the event"),
            'start_date': _("Date of the activity"),
            'website': _("Event website"),
            'summary': _("Summary of the communication"),
            'participating_proof': _("Attestation of the communication"),
        }


class ServiceForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/service.html"
    type = ConfigurableActivityTypeField("service_types", label=_("Type of activity"))

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'organizing_institution',
            'hour_volume',
            'participating_proof',
            'ects',
            'comment',
        ]
        labels = {
            'title': _("Name of the activity"),
            'subtitle': _("Description of the activity"),
            'participating_proof': _("Proof (if needed)"),
            'organizing_institution': _("Institution"),
        }


class SeminarForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/seminar.html"
    type = ConfigurableActivityTypeField("seminar_types", label=_("Type of activity"))

    class Meta:
        fields = [
            'type',
            'title',
            'start_date',
            'end_date',
            'hour_volume',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Name of the activity"),
            'participating_proof': _("Proof of participation for the whole activity"),
        }


class SeminarCommunicationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/seminar_communication.html"

    class Meta:
        fields = [
            'title',
            'start_date',
            'is_online',
            'country',
            'city',
            'organizing_institution',
            'website',
            'authors',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Title of the communication"),
            'start_date': _("Date of presentation"),
            'authors': _("Speaker"),
            'participating_proof': _("Certificate of participation in the presentation"),
        }


class ValorisationForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/valorisation.html"

    class Meta:
        fields = [
            'title',
            'subtitle',
            'summary',
            'participating_proof',
            'ects',
        ]
        labels = {
            'title': _("Title"),
            'subtitle': _("Description"),
            'summary': _("Detailed curriculum vitae"),
            'participating_proof': _("Proof"),
        }


class BatchActivityForm(forms.Form):
    activity_ids = forms.MultipleChoiceField()

    def __init__(self, uuids=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activity_ids'].choices = zip(uuids, uuids)
