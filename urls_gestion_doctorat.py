# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.urls import include, path

from admission.contrib.views.autocomplete import InstituteAutocomplete
from admission.contrib.views.common.detail_tabs.accounting import (
    AdmissionAccountingDetailView,
)
from admission.contrib.views.common.detail_tabs.coordonnees import (
    AdmissionCoordonneesDetailView,
)
from admission.contrib.views.common.detail_tabs.curriculum import (
    AdmissionCurriculumDetailView,
)
from admission.contrib.views.common.detail_tabs.curriculum_experiences import (
    AdmissionCurriculumEducationalExperienceDetailView,
    AdmissionCurriculumProfessionalExperienceDetailView,
)
from admission.contrib.views.common.detail_tabs.languages import (
    AdmissionLanguagesDetailView,
)
from admission.contrib.views.common.detail_tabs.person import AdmissionPersonDetailView
from admission.contrib.views.common.detail_tabs.training_choice import (
    TrainingChoiceDetailView,
)
from admission.contrib.views.doctorate.cotutelle import (
    DoctorateAdmissionCotutelleDetailView,
)
from admission.contrib.views.doctorate.project import (
    DoctorateAdmissionProjectDetailView,
)
from admission.contrib.views.doctorate.supervision import (
    DoctorateAdmissionSupervisionDetailView,
)
from admission.contrib.views.list import DoctorateAdmissionMemberListView

"""URLs of pages accessible to members of the supervision groups of the PhD admissions."""

app_name = 'gestion_doctorat'

curriculum_patterns = (
    [
        path(
            'professional/<uuid:experience_id>/',
            AdmissionCurriculumProfessionalExperienceDetailView.as_view(),
            name='professional_read',
        ),
        path(
            'educational/<uuid:experience_id>/',
            AdmissionCurriculumEducationalExperienceDetailView.as_view(),
            name='educational_read',
        ),
    ],
    'curriculum',
)

doctorate_patterns = (
    [
        path('training_choice', TrainingChoiceDetailView.as_view(), name='training-choice'),
        path('person', AdmissionPersonDetailView.as_view(), name='person'),
        path('coordonnees', AdmissionCoordonneesDetailView.as_view(), name='coordonnees'),
        path('curriculum', AdmissionCurriculumDetailView.as_view(), name='curriculum'),
        path('curriculum/', include(curriculum_patterns), name='curriculum'),
        path('languages', AdmissionLanguagesDetailView.as_view(), name='languages'),
        path('accounting', AdmissionAccountingDetailView.as_view(), name='accounting'),
        path('project', DoctorateAdmissionProjectDetailView.as_view(), name='project'),
        path('cotutelle', DoctorateAdmissionCotutelleDetailView.as_view(), name='cotutelle'),
        path('supervision', DoctorateAdmissionSupervisionDetailView.as_view(), name='supervision'),
    ],
    'doctorate',
)

autocomplete_patterns = (
    [
        path('institute', InstituteAutocomplete.as_view(), name='institute'),
    ],
    'autocomplete',
)

urlpatterns = [
    path('<str:pk>/', include(doctorate_patterns)),
    path('autocomplete/', include(autocomplete_patterns)),
    path('', DoctorateAdmissionMemberListView.as_view(), name='supervised-list'),
]
