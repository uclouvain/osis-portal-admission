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

from dal import autocomplete
from django import forms
from django.utils.translation import get_language, gettext_lazy as _, pgettext_lazy

from admission.contrib.enums.training import ChoixComiteSelection, ChoixStatutPublication, ChoixTypeEpreuve
from admission.contrib.forms import (
    CustomDateInput,
    SelectOrOtherField,
    get_academic_years_choices,
)
from admission.services.reference import AcademicYearService
from osis_document.contrib import FileUploadField

__all__ = [
    "BatchActivityForm",
    "CommunicationForm",
    "ConferenceCommunicationForm",
    "ConferenceForm",
    "ConferencePublicationForm",
    "CourseForm",
    "PaperForm",
    "PublicationForm",
    "ResidencyCommunicationForm",
    "ResidencyForm",
    "SeminarCommunicationForm",
    "SeminarForm",
    "ServiceForm",
    "ValorisationForm",
]

INSTITUTION_UCL = "UCLouvain"


class ConfigurableActivityTypeField(SelectOrOtherField):
    select_class = forms.CharField

    def __init__(self, source: str = '', *args, **kwargs):
        self.source = source
        super().__init__(*args, **kwargs)

    def get_bound_field(self, form, field_name):
        # Update radio choices from CDD configuration
        values = form.config_types.get(self.source, {}).get(get_language(), [])
        self.widget.widgets[0].choices = list(zip(values, values)) + [('other', _("Other"))]
        return super().get_bound_field(form, field_name)


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

    def __init__(self, config_types=None, person=None, *args, **kwargs) -> None:
        self.person = person
        self.config_types = config_types or {}
        super().__init__(*args, **kwargs)
        # Remove unneeded fields
        for field_name in list(self.fields.keys()):
            if field_name not in self.Meta.fields:
                del self.fields[field_name]
        # Make all fields not required and apply label overrides
        labels = getattr(self.Meta, 'labels', {})
        for field_name in self.fields:
            # if not isinstance(self.fields[field_name], ConfigurableActivityTypeField):
            if field_name != 'type':
                self.fields[field_name].required = False
            self.fields[field_name].label = labels.get(field_name, self.fields[field_name].label)


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
    type = SelectOrOtherField(
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
    subtype = SelectOrOtherField(
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


class CourseForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/course.html"
    type = ConfigurableActivityTypeField("course_types", label=_("Type of activity"))
    subtitle = forms.CharField(
        label=_("Course code (if needed)"),
        max_length=200,
        required=False,
    )
    organizing_institution = SelectOrOtherField(choices=[INSTITUTION_UCL], label=_("Institution"))
    academic_year = forms.ChoiceField(
        label=_("Academic year"),
        widget=autocomplete.ListSelect2(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert from dates to year if UCLouvain
        if self.data.get("organizing_institution", self.initial.get('organizing_institution')) == INSTITUTION_UCL:
            self.fields['academic_year'].initial = self.get_academic_year()
        self.fields['academic_year'].choices = get_academic_years_choices(self.person)

    def get_academic_year(self):
        start_date = self.data.get("start_date", self.initial.get('start_date'))
        end_date = self.data.get("end_date", self.initial.get('end_date'))
        for academic_year in AcademicYearService.get_academic_years(self.person):
            if academic_year.start_date == start_date and academic_year.end_date == end_date:
                return academic_year.year

    def get_academic_year_dates(self, year):
        for academic_year in AcademicYearService.get_academic_years(self.person):
            if academic_year.year == year:
                return academic_year.start_date, academic_year.end_date

    def clean(self):
        cleaned_data = super().clean()
        # Convert from academic year to dates if UCLouvain
        if cleaned_data.get('organizing_institution') == INSTITUTION_UCL and cleaned_data.get('academic_year'):
            year = self.get_academic_year_dates(cleaned_data['academic_year'])
            cleaned_data['start_date'], cleaned_data['end_date'] = year or (None, None)
        return cleaned_data

    class Meta:
        fields = [
            'type',
            'title',
            'subtitle',
            'organizing_institution',
            'start_date',
            'end_date',
            'academic_year',
            'hour_volume',
            'authors',
            'ects',
            'participating_proof',
            'comment',
        ]
        labels = {
            'title': _("Name of the activity"),
            'authors': _("Course owner if applicable"),
            'participating_proof': _("Proof of participation or success"),
        }


class PaperForm(ActivityFormMixin, forms.Form):
    template_name = "admission/doctorate/forms/training/paper.html"
    type = forms.ChoiceField(label=_("Type of paper"), choices=ChoixTypeEpreuve.choices())

    class Meta:
        fields = [
            'type',
            'ects',
            'comment',
        ]


class BatchActivityForm(forms.Form):
    activity_ids = forms.MultipleChoiceField()

    def __init__(self, uuids=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['activity_ids'].choices = zip(uuids, uuids)