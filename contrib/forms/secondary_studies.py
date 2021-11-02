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
    DiplomaTypes,
    DiplomaResults,
    EducationalType,
    ForeignDiplomaTypes,
)
from admission.contrib.forms import get_country_initial_choices, EMPTY_CHOICE, get_language_initial_choices
from admission.services.reference import AcademicYearService


class DoctorateAdmissionEducationForm(forms.Form):
    got_diploma = forms.BooleanField(
        label=_("Did you obtain a high school diploma or will you receive this kind of diploma still this year?"),
        widget=forms.RadioSelect(
            choices=[
                (True, _('Yes')),
                (False, _('No')),
            ],
        ),
        required=False,
    )
    academic_graduation_year = forms.IntegerField(
        label=_("Please mention the academic graduation year"),
        widget=autocomplete.ListSelect2,
        required=False,
    )
    diploma_type = forms.ChoiceField(
        label=_("Type of high school diploma"),
        choices=DiplomaTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    result = forms.ChoiceField(
        label="",
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        got_diploma = cleaned_data.get("got_diploma")

        if got_diploma:
            field_required_msg = _("This field is required")
            academic_graduation_year = cleaned_data.get("academic_graduation_year")
            diploma_type = cleaned_data.get("diploma_type")
            result = cleaned_data.get("result")
            if not academic_graduation_year:
                self.add_error('academic_graduation_year', field_required_msg)
            if not diploma_type:
                self.add_error('diploma_type', field_required_msg)
            if not result:
                self.add_error('result', field_required_msg)

        return cleaned_data

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
            self.fields["got_diploma"].initial = True
            self.fields["diploma_type"].initial = (
                DiplomaTypes.BELGIAN.name if belgian_diploma else DiplomaTypes.FOREIGN.name
            )
            self.fields["academic_graduation_year"].initial = diploma.get("academic_graduation_year")
            self.fields["result"].initial = diploma.get("result")


class DoctorateAdmissionEducationBelgianDiplomaForm(forms.Form):
    community = forms.ChoiceField(
        label=_("In what Community did (do) you follow last year of high school?"),
        choices=BelgianCommunitiesOfEducation.choices(),
        widget=forms.RadioSelect,
    )
    educational_type = forms.ChoiceField(
        label=_("What type of education did (do) you follow?"),
        choices=EducationalType.choices(),
        widget=forms.RadioSelect,
        required=False,
    )
    educational_other = forms.CharField(
        label=_(">> Other education, to specify"),
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
    institute = forms.CharField(required=False)
    other_institute = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get("community")
        educational_type = cleaned_data.get("educational_type")
        educational_other = cleaned_data.get("educational_other")

        # FIXME those two following fields are required, but can't be validated without `required=False`
        course_repeat = cleaned_data.get("course_repeat")
        course_orientation = cleaned_data.get("course_orientation")
        required_field_error_msg = _("This field is required.")
        if course_repeat is None:
            self.add_error("course_repeat", required_field_error_msg)
        if course_orientation is None:
            self.add_error("course_orientation", required_field_error_msg)

        if community == BelgianCommunitiesOfEducation.FRENCH_SPEAKING.name and not (educational_type or educational_other):
            educational_type_error_msg = _("Educational type is required with this community of education")
            self.add_error("educational_type", educational_type_error_msg)

        institute = cleaned_data.get("institute")
        other_institute = cleaned_data.get("other_institute")
        institute_error_msg = _("Please set one of institute or other institute fields")
        if institute == "" and other_institute == "":
            self.add_error("institute", institute_error_msg)
            self.add_error("other_institute", institute_error_msg)

        return cleaned_data


class DoctorateAdmissionEducationScheduleForm(forms.Form):
    # ancient language
    latin = forms.IntegerField(label=_("Latin"), min_value=0)
    greek = forms.IntegerField(label=_("Greek"), min_value=0)
    # sciences
    chemistry = forms.IntegerField(label=_("Chemistry"), min_value=0)
    physic = forms.IntegerField(label=_("Physic"), min_value=0)
    biology = forms.IntegerField(label=_("Biology"), min_value=0)
    # modern languages
    german = forms.IntegerField(label=_("German"), min_value=0)
    dutch = forms.IntegerField(label=_("Dutch"), min_value=0)
    english = forms.IntegerField(label=_("English"), min_value=0)
    french = forms.IntegerField(label=_("french"), min_value=0)
    modern_languages_other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other language, please specify"),
        required=False,
    )
    modern_languages_other_hours = forms.IntegerField(required=False)
    # other disciplines
    mathematics = forms.IntegerField(label=_("Mathematics"), min_value=0)
    it = forms.IntegerField(label=_("IT"), min_value=0)
    social_sciences = forms.IntegerField(label=_("Social sciences"), min_value=0)
    economic_sciences = forms.IntegerField(label=_("Economic sciences"), min_value=0)
    other_label = forms.CharField(
        label=_("Other"),
        help_text=_("If other optional domains, please specify"),
        required=False,
    )
    other_hours = forms.IntegerField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        label_required_error_msg = "label is required"
        hours_required_error_msg = "hours are required"

        modern_languages_other_label = cleaned_data.get("modern_languages_other_label")
        modern_languages_other_hours = cleaned_data.get("modern_languages_other_hours")
        if modern_languages_other_label and not modern_languages_other_hours:
            self.add_error("modern_languages_other_hours", hours_required_error_msg)
        if not modern_languages_other_label and modern_languages_other_hours:
            self.add_error("modern_languages_other_label", label_required_error_msg)

        other_label = cleaned_data.get("other_label")
        other_hours = cleaned_data.get("other_hours")
        if other_label and not other_hours:
            self.add_error("other_hours", hours_required_error_msg)
        if not other_label and other_hours:
            self.add_error("other_label", label_required_error_msg)

        return cleaned_data


class DoctorateAdmissionEducationForeignDiplomaForm(forms.Form):
    foreign_diploma_type = forms.ChoiceField(
        label=_("What diploma did you get (or will you get) ?"),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
    )
    linguistic_regime = forms.CharField(
        label=_("Linguistic regime"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
    )
    other_linguistic_regime = forms.CharField(
        label=_("If other linguistic regime, please clarify"),
        required=False,
    )
    country = forms.CharField(
        label=_("Organizing country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
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
