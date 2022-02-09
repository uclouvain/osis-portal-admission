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

from .autocomplete import *
from .cancel import DoctorateAdmissionCancelView
from .detail_tabs.coordonnees import DoctorateAdmissionCoordonneesDetailView, DoctorateAdmissionCoordonneesDetailView
from .detail_tabs.curriculum import DoctorateAdmissionCurriculumDetailView
from .detail_tabs.person import DoctorateAdmissionPersonDetailView
from .detail_tabs.project import DoctorateAdmissionProjectDetailView
from .detail_tabs.supervision import DoctorateAdmissionApprovalByPdfView
from .form_tabs.coordonnees import DoctorateAdmissionCoordonneesFormView
from .form_tabs.curriculum import DoctorateAdmissionCurriculumFormView
from .form_tabs.person import DoctorateAdmissionPersonFormView
from .form_tabs.project import DoctorateAdmissionProjectFormView
from .form_tabs.supervision import DoctorateAdmissionRemoveActorView
from .list import *
from .signatures import (
    DoctorateAdmissionRequestSignaturesView,
    DoctorateAdmissionRequestSignaturesView,
    DoctorateAdmissionRequestSignaturesView,
)

__all__ = [
    "DoctorateAutocomplete",
    "DoctorateAdmissionListView",
    "DoctorateAdmissionProjectFormView",
    "DoctorateAdmissionProjectDetailView",
    "DoctorateAdmissionPersonFormView",
    "DoctorateAdmissionPersonDetailView",
    "DoctorateAdmissionCoordonneesFormView",
    "DoctorateAdmissionCoordonneesDetailView",
    "DoctorateAdmissionRemoveActorView",
    "DoctorateAdmissionCancelView",
    "DoctorateAdmissionRequestSignaturesView",
    "DoctorateAdmissionCurriculumFormView",
    "DoctorateAdmissionCurriculumDetailView",
    "DoctorateAdmissionApprovalByPdfView",
]
