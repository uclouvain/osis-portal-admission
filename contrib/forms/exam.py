# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django import forms
from django.utils.translation import gettext_lazy as _

from admission.contrib.forms import AdmissionFileUploadField as FileUploadField
from admission.contrib.forms import autocomplete, get_past_academic_years_choices


class ExamForm(forms.Form):
    certificate = FileUploadField(
        label=_("Certificate"),
        max_files=1,
        required=False,
    )
    year = forms.TypedChoiceField(
        label=_('Year of obtaining this proof'),
        widget=autocomplete.Select2(),
        coerce=int,
        required=False,
    )

    def __init__(self, person, is_valuated, certificate_title, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['certificate'].label = certificate_title
        self.fields['year'].choices = get_past_academic_years_choices(
            person,
            format_label_function=lambda academic_year: str(academic_year.year + 1),
        )
        if is_valuated:
            self.fields['certificate'].disabled = True
            self.fields['year'].disabled = True
