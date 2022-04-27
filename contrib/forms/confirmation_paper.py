# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_document.contrib import FileUploadField

from admission.contrib.forms import CustomDateInput


class PromoterConfirmationPaperForm(forms.Form):
    proces_verbal_ca = FileUploadField(
        label=_('Report of the supervisory panel'),
        required=False,
        max_files=1,
    )
    avis_renouvellement_mandat_recherche = FileUploadField(
        label=_('Opinion on the renewal of the research mandate'),
        required=False,
        max_files=1,
        help_text=_("To be uploaded if you have a F.R.S.-FNRS (including Télévie), FRIA or FRESH grant. "
                    "The framework for this opinion is provided by your research fund."),
    )


class ConfirmationPaperForm(PromoterConfirmationPaperForm):
    date = forms.DateField(
        label=_('Date of confirmation'),
        required=True,
        widget=CustomDateInput(),
    )
    rapport_recherche = FileUploadField(
        label=_('Research report'),
        required=False,
        max_files=1,
    )
