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
    )
    academic_graduation_year = forms.ChoiceField(
        label=_("Please mention the academic graduation year"),
        widget=autocomplete.ListSelect2,
    )
    diploma_type = forms.ChoiceField(
        label=_("Type of high school diploma"),
        choices=DiplomaTypes.choices(),
        widget=forms.RadioSelect,
    )
    result = forms.ChoiceField(
        label="",
        choices=DiplomaResults.choices(),
        widget=forms.RadioSelect,
    )

    class Media:
        js = ("dependsOn.min.js",)

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        year_choices = tuple(
            (academic_year.year, "{}-{}".format(academic_year.year, str(academic_year.year + 1)[2:]))
            for academic_year in AcademicYearService.get_academic_years(person)
        )
        self.fields["academic_graduation_year"].choices = EMPTY_CHOICE + year_choices

        diploma = None
        if self.initial.get("belgian_diploma"):
            diploma = "BELGIAN"
        elif self.initial.get("foreign_diploma"):
            diploma = "FOREIGN"
        # Tick the got_diploma checkbox only if there is a saved diploma
        # and select the correct related type
        if diploma:
            self.fields["got_diploma"].initial = True
            self.fields["diploma_type"].initial = diploma


class DoctorateAdmissionEducationBelgianDiplomaForm(forms.Form):
    community = forms.ChoiceField(
        label=_("In what Community did (do) you follow last year of high school?"),
        choices=BelgianCommunitiesOfEducation.choices(),
        widget=forms.RadioSelect,
        required=False,
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
    course_repeat = forms.BooleanField(
        label=_("Did you repeat certain study years during your studies?"),
        widget=forms.RadioSelect(
            choices=[
                (1, _('Yes')),
                (0, _('No')),
            ],
        ),
        required=False,
    )
    course_orientation = forms.BooleanField(
        label=_("Did you change of orientation during your studies?"),
        widget=forms.RadioSelect(
            choices=[
                (1, _('Yes')),
                (0, _('No')),
            ],
        ),
        required=False,
    )
    # TODO institute & other_institute
    institute = forms.CharField(required=False)
    other_institute = forms.CharField(required=False)


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


class DoctorateAdmissionEducationForeignDiplomaForm(forms.Form):
    foreign_diploma_type = forms.ChoiceField(
        label=_("What diploma did you get (or will you get) ?"),
        choices=ForeignDiplomaTypes.choices(),
        widget=forms.RadioSelect,
    )
    linguistic_regime = forms.ChoiceField(
        label=_("Linguistic regime"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:language"),
    )
    other_linguistic_regime = forms.CharField(
        label=_("If other linguistic regime, please clarify"),
        required=False,
    )
    country = forms.ChoiceField(
        label=_("Organizing country"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:country"),
    )

    def __init__(self, person=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = get_country_initial_choices(self.initial.get('country'), person)
        self.fields['linguistic_regime'].choices = get_language_initial_choices(self.initial.get('linguistic_regime'), person)
