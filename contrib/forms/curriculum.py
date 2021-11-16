# ##############################################################################
# 
#     OSIS stands for Open Student Information System. It's an application
#     designed to manage the core business of higher education institutions,
#     such as universities, faculties, institutes and professional schools.
#     The core business involves the administration of students, teachers,
#     courses, programs and so on.
# 
#     Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
# 
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     A copy of this license - GNU General Public License - is available
#     at the root of the source code of this program.  If not,
#     see http://www.gnu.org/licenses/.
# 
# ##############################################################################
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _

from admission.contrib.enums.curriculum import CourseTypes
from admission.contrib.forms import EMPTY_CHOICE
from admission.services.reference import AcademicYearService


class DoctorateAdmissionCurriculumForm(forms.Form):
    academic_graduation_year = forms.IntegerField(
        label=_("Please mention the academic graduation year"),
        widget=autocomplete.ListSelect2,
        required=False,
    )
    course_type = forms.ChoiceField(
        label=_("Type of high school diploma"),
        choices=CourseTypes.choices(),
        widget=forms.RadioSelect,
        required=False,
    )

    def __init__(self, *args, person=None, **kwargs):
        super().__init__(*args, **kwargs)
        year_choices = tuple(
            (academic_year.year, "{}-{}".format(academic_year.year, str(academic_year.year + 1)[2:]))
            for academic_year in AcademicYearService.get_academic_years(person)
        )
        self.fields["academic_graduation_year"].widget.choices = EMPTY_CHOICE + year_choices
        # FIXME Pas normal ça ...
        self.fields["academic_graduation_year"].initial = self.initial.get("academic_graduation_year")


DoctorateAdmissionCurriculumFormSet = forms.formset_factory(
    DoctorateAdmissionCurriculumForm,
    extra=1,
)
