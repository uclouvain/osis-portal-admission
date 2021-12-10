# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

from admission.contrib.enums.secondary_studies import (
    BelgianCommunitiesOfEducation,
    DiplomaResults,
    DiplomaTypes,
    EDUCATIONAL_TYPES,
    Equivalence,
    ForeignDiplomaTypes,
    GotDiploma,
)
from admission.contrib.forms import (
    EMPTY_CHOICE,
    get_country_initial_choices,
    get_language_initial_choices,
)
from admission.services.reference import AcademicYearService

FIELD_REQUIRED_MESSAGE = _("This field is required.")


class DoctorateAdmissionEducationForm(forms.Form):
    got_diploma = forms.ChoiceField(
        label=_("Do you have a high school diploma?"),
        choices=GotDiploma.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    academic_graduation_year = forms.IntegerField(
        label=_("Please mention the academic graduation year"),
        widget=autocomplete.ListSelect2,
        required=False,
    )
    diploma_type = forms.ChoiceField(
        label=_("This is a diploma from"),
        choices=DiplomaTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )

    class Media:
        js = ("dependsOn.min.js",)

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        year_choices = tuple(
            (academic_year.year, "{}-{}".format(academic_year.year, str(academic_year.year + 1)[2:]))
            for academic_year in AcademicYearService.get_academic_years(person)
        )
        self.fields["academic_graduation_year"].widget.choices = EMPTY_CHOICE + year_choices

        belgian_diploma = self.initial.get("belgian_diploma")
        foreign_diploma = self.initial.get("foreign_diploma")
        diploma = belgian_diploma or foreign_diploma
        # Tick the got_diploma checkbox only if there is a saved diploma
        # and select the correct related type
        if diploma:
            self.fields["got_diploma"].initial = GotDiploma.YES.name
            self.fields["diploma_type"].initial = (
                DiplomaTypes.BELGIAN.name if belgian_diploma else DiplomaTypes.FOREIGN.name
            )
            self.fields["academic_graduation_year"].initial = diploma.get("academic_graduation_year")
        else:
            self.fields["got_diploma"].initial = GotDiploma.NO.name

    def clean(self):
        cleaned_data = super().clean()

        got_diploma = cleaned_data.get("got_diploma")
        if got_diploma in [GotDiploma.THIS_YEAR.name, GotDiploma.YES.name]:
            if got_diploma == GotDiploma.YES.name and not cleaned_data.get("academic_graduation_year"):
                self.add_error('academic_graduation_year', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get("diploma_type"):
                self.add_error('diploma_type', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class DoctorateAdmissionEducationBelgianDiplomaForm(forms.Form):
    community = forms.ChoiceField(
        label=_("In what Community did (do) you follow last year of high school?"),
        choices=BelgianCommunitiesOfEducation.choices(),
        widget=autocomplete.ListSelect2,
    )
    educational_type = forms.ChoiceField(
        label=_("What type of education did (do) you follow?"),
        choices=EDUCATIONAL_TYPES,
        widget=autocomplete.ListSelect2,
        required=False,
    )
    educational_other = forms.CharField(
        label=_("If you cannot find your educational type, please clarify below"),
        required=False,
    )
    course_repeat = forms.NullBooleanField(
        label=_("Did you repeat certain study years during your studies?"),
        widget=forms.RadioSelect(
            choices=[
                (True, _('Yes')),
                (False, _('No')),
            ],
        ),
        required=False,
    )
    course_orientation = forms.NullBooleanField(
        label=_("Did you change of orientation during your studies?"),
        widget=forms.RadioSelect(
            choices=[
                (True, _('Yes')),
                (False, _('No')),
            ],
        ),
        required=False,
    )
    # TODO institute & other_institute
    institute = forms.CharField(label=_("Institute"), required=False)
    other_institute = forms.CharField(
        label=_("If you cannot find your institute, please clarify below"),
        required=False,
    )
    result = forms.ChoiceField(
        label=_("At which result level do you consider yourself?"),
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get("community")
        educational_type = cleaned_data.get("educational_type")
        educational_other = cleaned_data.get("educational_other")

        course_repeat = cleaned_data.get("course_repeat")
        course_orientation = cleaned_data.get("course_orientation")
        if course_repeat is None:
            self.add_error("course_repeat", FIELD_REQUIRED_MESSAGE)
        if course_orientation is None:
            self.add_error("course_orientation", FIELD_REQUIRED_MESSAGE)

        if (
            community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name
            and not (educational_type or educational_other)
        ):
            self.add_error("educational_type", _("Educational type is required with this community of education"))

        if not cleaned_data.get("institute") and not cleaned_data.get("other_institute"):
            institute_error_msg = _("Please set one of institute or other institute fields")
            self.add_error("institute", institute_error_msg)
            self.add_error("other_institute", institute_error_msg)

        if not cleaned_data.get("result"):
            self.add_error('result', FIELD_REQUIRED_MESSAGE)

        return cleaned_data


class HourField(forms.IntegerField):
    def __init__(self, *, max_value=None, min_value=0, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(max_value=max_value, min_value=min_value, **kwargs)


class DoctorateAdmissionEducationScheduleForm(forms.Form):
    # ancient language
    latin = HourField(label=_("Latin"))
    greek = HourField(label=_("Greek"))
    # sciences
    chemistry = HourField(label=_("Chemistry"))
    physic = HourField(label=_("Physic"))
    biology = HourField(label=_("Biology"))
    # modern languages
    german = HourField(label=_("German"))
    dutch = HourField(label=_("Dutch"))
    english = HourField(label=_("English"))
    french = HourField(label=_("French"))
    modern_languages_other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other language, please specify"),
        required=False,
    )
    modern_languages_other_hours = HourField()
    # other disciplines
    mathematics = HourField(label=_("Mathematics"))
    it = HourField(label=_("IT"))
    social_sciences = HourField(label=_("Social sciences"))
    economic_sciences = HourField(label=_("Economic sciences"))
    other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other optional domains, please specify"),
        required=False,
    )
    other_hours = HourField()

    def get_initial_for_field(self, field, field_name):
        # Set all hours fields to None if initial is 0, so that nothing is displayed in field
        if isinstance(field, HourField) and not self.initial.get(field_name):
            return None
        return super().get_initial_for_field(field, field_name)

    def clean(self):
        cleaned_data = super().clean()

        # At least a field is required
        if not any(cleaned_data.get(f) for f in self.fields):
            self.add_error(None, _("A field of the schedule must at least be set."))

        dependent_fields = [
            ("modern_languages_other_label", "modern_languages_other_hours"),
            ("other_label", "other_hours"),
        ]

        for label_field, hours_field in dependent_fields:
            label = cleaned_data.get(label_field)
            hours = cleaned_data.get(hours_field)
            if label and not hours:
                self.add_error(hours_field, _("hours are required"))
            if not label and hours:
                self.add_error(label_field, _("label is required"))

        # Set all hours fields to 0 if they have no value, because API rejects None
        for field in self.fields:
            if isinstance(self.fields[field], HourField) and not cleaned_data.get(field):
                cleaned_data[field] = 0

        return cleaned_data


class DoctorateAdmissionEducationForeignDiplomaForm(forms.Form):
    foreign_diploma_type = forms.ChoiceField(
        label=_("What diploma did you get (or will you get) ?"),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
    )
    equivalence = forms.ChoiceField(
        label=_(
            "Is this diploma subject to an equivalence decision by the services of the French community of Belgium?"
        ),
        choices=Equivalence.choices(),
        widget=forms.RadioSelect,
    )
    linguistic_regime = forms.CharField(
        label=_("Linguistic regime"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
        required=False,
    )
    other_linguistic_regime = forms.CharField(
        label=_("If you cannot find your linguistic regime, please clarify below"),
        required=False,
    )
    country = forms.CharField(
        label=_("Organizing country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )
    result = forms.ChoiceField(
        label=_("What result did you get?"),
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
        required=False,
    )

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].widget.choices = get_country_initial_choices(
            self.data.get(self.add_prefix("country"), self.initial.get("country")),
            person,
        )
        self.fields['linguistic_regime'].widget.choices = get_language_initial_choices(
            self.data.get(self.add_prefix("linguistic_regime"), self.initial.get("linguistic_regime")),
            person,
        )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("linguistic_regime") and not cleaned_data.get("other_linguistic_regime"):
            self.add_error("linguistic_regime", _("Please set either the linguistic regime or other field."))
        if not cleaned_data.get("result"):
            self.add_error('result', FIELD_REQUIRED_MESSAGE)
        return cleaned_data
