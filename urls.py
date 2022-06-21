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
from django.urls import include, path
from django.views.generic import RedirectView

from .contrib import views

app_name = "admission"

autocomplete_paths = [
    path("tutor/", views.TutorAutocomplete.as_view(), name="tutor"),
    path("person/", views.PersonAutocomplete.as_view(), name="person"),
    path("doctorate/", views.DoctorateAutocomplete.as_view(), name="doctorate"),
    path("country/", views.CountryAutocomplete.as_view(), name="country"),
    path("city/", views.CityAutocomplete.as_view(), name="city"),
    path("language/", views.LanguageAutocomplete.as_view(), name="language"),
    path("institute/", views.InstituteAutocomplete.as_view(), name="institute"),
    path("institute-location/", views.InstituteLocationAutocomplete.as_view(), name="institute-location"),
]

creation_paths = [
    path("person", views.DoctorateAdmissionPersonFormView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesFormView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumFormView.as_view(), name="curriculum"),
    path('curriculum/<uuid:experience_id>/', views.DoctorateAdmissionCurriculumFormView.as_view(), name='curriculum'),
    path("education", views.DoctorateAdmissionEducationFormView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesFormView.as_view(), name="languages"),
    path("project", views.DoctorateAdmissionProjectFormView.as_view(), name="project"),
]

update_paths = [
    path("person", views.DoctorateAdmissionPersonFormView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesFormView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumFormView.as_view(), name="curriculum"),
    path('curriculum/<uuid:experience_id>/', views.DoctorateAdmissionCurriculumFormView.as_view(), name='curriculum'),
    path("education", views.DoctorateAdmissionEducationFormView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesFormView.as_view(), name="languages"),
    path("project", views.DoctorateAdmissionProjectFormView.as_view(), name="project"),
    path("cotutelle", views.DoctorateAdmissionCotutelleFormView.as_view(), name="cotutelle"),
    path("supervision", views.DoctorateAdmissionSupervisionFormView.as_view(), name="supervision"),
    path("confirmation", views.DoctorateAdmissionConfirmationPaperFormView.as_view(), name="confirmation-paper"),
    path("extension-request", views.DoctorateAdmissionExtensionRequestFormView.as_view(), name="extension-request"),
]

detail_paths = [
    path("person", views.DoctorateAdmissionPersonDetailView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesDetailView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumDetailView.as_view(), name="curriculum"),
    path("education", views.DoctorateAdmissionEducationDetailView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesDetailView.as_view(), name="languages"),
    path("project", views.DoctorateAdmissionProjectDetailView.as_view(), name="project"),
    path("cotutelle", views.DoctorateAdmissionCotutelleDetailView.as_view(), name="cotutelle"),
    path("supervision", views.DoctorateAdmissionSupervisionDetailView.as_view(), name="supervision"),
    path("request_signatures", views.DoctorateAdmissionRequestSignaturesView.as_view(), name="request-signatures"),
    path('remove-member/<type>/<matricule>', views.DoctorateAdmissionRemoveActorView.as_view(), name='remove-actor'),
    path('approve-by-pdf', views.DoctorateAdmissionApprovalByPdfView.as_view(), name='approve-by-pdf'),
    path("update/", include((update_paths, "update"))),
    path("cancel", views.DoctorateAdmissionCancelView.as_view(), name="cancel"),
    path("confirm", views.DoctorateAdmissionConfirmFormView.as_view(), name="confirm"),
    path("confirmation", views.DoctorateAdmissionConfirmationPaperDetailView.as_view(), name="confirmation-paper"),
    path(
        "confirmation-paper-canvas",
        views.DoctorateAdmissionConfirmationPaperCanvasExportView.as_view(),
        name="confirmation-paper-canvas",
    ),
    path("extension-request", views.DoctorateAdmissionExtensionRequestDetailView.as_view(), name="extension-request"),
]

urlpatterns = [
    # Lists
    path("doctorate/", views.DoctorateAdmissionListView.as_view(), name="doctorate-list"),
    path("supervised/", views.DoctorateAdmissionMemberListView.as_view(), name="supervised-list"),
    # Autocompletes
    path("autocomplete/", include((autocomplete_paths, "autocomplete"))),
    # Creation
    path(
        "doctorate/create/",
        RedirectView.as_view(pattern_name="admission:doctorate-create:project"),
        name="doctorate-create",
    ),
    path("doctorate/create/", include((creation_paths, "doctorate-create"))),
    # Detail
    path("doctorate/<uuid:pk>/", include((detail_paths, "doctorate"))),
]
