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
    path("high-school/", views.HighSchoolAutocomplete.as_view(), name="high-school"),
    path("diploma/", views.DiplomaAutocomplete.as_view(), name="diploma"),
    path("learning-unit-years/", views.LearningUnitYearsAutocomplete.as_view(), name="learning-unit-years"),
    path("superior-non-university/", views.SuperiorNonUniversityAutocomplete.as_view(), name="superior-non-university"),
    path("general-education/", views.GeneralEducationAutocomplete.as_view(), name="general-education"),
    path("continuing-education/", views.ContinuingEducationAutocomplete.as_view(), name="continuing-education"),
    path("scholarship/", views.ScholarshipAutocomplete.as_view(), name="scholarship"),
]

curriculum_read_paths = [
    path(
        "educational/<uuid:experience_id>/",
        views.DoctorateAdmissionCurriculumEducationalExperienceDetailView.as_view(),
        name="educational_read",
    ),
    path(
        "professional/<uuid:experience_id>/",
        views.DoctorateAdmissionCurriculumProfessionalExperienceDetailView.as_view(),
        name="professional_read",
    ),
]

curriculum_update_paths = [
    path(
        "educational/<uuid:experience_id>/update",
        views.DoctorateAdmissionCurriculumEducationalExperienceFormView.as_view(),
        name="educational_update",
    ),
    path(
        "educational/<uuid:experience_id>/delete",
        views.DoctorateAdmissionCurriculumEducationalExperienceDeleteView.as_view(),
        name="educational_delete",
    ),
    path(
        "educational/create",
        views.DoctorateAdmissionCurriculumEducationalExperienceFormView.as_view(),
        name="educational_create",
    ),
    path(
        "professional/<uuid:experience_id>/update",
        views.DoctorateAdmissionCurriculumProfessionalExperienceFormView.as_view(),
        name="professional_update",
    ),
    path(
        "professional/<uuid:experience_id>/delete",
        views.DoctorateAdmissionCurriculumProfessionalExperienceDeleteView.as_view(),
        name="professional_delete",
    ),
    path(
        "professional/create",
        views.DoctorateAdmissionCurriculumProfessionalExperienceFormView.as_view(),
        name="professional_create",
    ),
]

creation_paths = [
    path("person", views.DoctorateAdmissionPersonFormView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesFormView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumFormView.as_view(), name="curriculum"),
    path("curriculum/", include((curriculum_update_paths, "curriculum"))),
    path("education", views.DoctorateAdmissionEducationFormView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesFormView.as_view(), name="languages"),
    # path("project", views.DoctorateAdmissionProjectFormView.as_view(), name="project"),
    path("training-choice", views.AdmissionTrainingChoiceFormView.as_view(), name="training-choice"),
]

update_paths = [
    path("person", views.DoctorateAdmissionPersonFormView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesFormView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumFormView.as_view(), name="curriculum"),
    path("curriculum/", include((curriculum_update_paths, "curriculum"))),
    path("education", views.DoctorateAdmissionEducationFormView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesFormView.as_view(), name="languages"),
    path("project", views.DoctorateAdmissionProjectFormView.as_view(), name="project"),
    path("cotutelle", views.DoctorateAdmissionCotutelleFormView.as_view(), name="cotutelle"),
    path("supervision", views.DoctorateAdmissionSupervisionFormView.as_view(), name="supervision"),
    path("confirmation", views.DoctorateAdmissionConfirmationPaperFormView.as_view(), name="confirmation-paper"),
    path("extension-request", views.DoctorateAdmissionExtensionRequestFormView.as_view(), name="extension-request"),
    path("accounting", views.DoctorateAdmissionAccountingFormView.as_view(), name="accounting"),
    path("training-choice", views.AdmissionTrainingChoiceFormView.as_view(), name="training-choice"),
]

training_paths = [
    path("add/<str:category>", views.TrainingActivityAddView.as_view(), name="add"),
    path('edit/<uuid:activity_id>', views.TrainingActivityEditView.as_view(), name='edit'),
    path("submit/<uuid:activity_id>", views.DoctoralTrainingListView.as_view(), name="submit"),
    path("assent/<uuid:activity_id>", views.TrainingActivityAssentView.as_view(), name="assent"),
    path("delete/<uuid:activity_id>", views.TrainingActivityDeleteView.as_view(), name="delete"),
]

doctorate_paths = [
    path("person", views.DoctorateAdmissionPersonDetailView.as_view(), name="person"),
    path("coordonnees", views.DoctorateAdmissionCoordonneesDetailView.as_view(), name="coordonnees"),
    path("curriculum", views.DoctorateAdmissionCurriculumDetailView.as_view(), name="curriculum"),
    path("curriculum/", include((curriculum_read_paths, "curriculum"))),
    path("education", views.DoctorateAdmissionEducationDetailView.as_view(), name="education"),
    path("languages", views.DoctorateAdmissionLanguagesDetailView.as_view(), name="languages"),
    path("project", views.DoctorateAdmissionProjectDetailView.as_view(), name="project"),
    path("cotutelle", views.DoctorateAdmissionCotutelleDetailView.as_view(), name="cotutelle"),
    path("supervision", views.DoctorateAdmissionSupervisionDetailView.as_view(), name="supervision"),
    path(
        "set-reference-promoter/<matricule>",
        views.DoctorateAdmissionSetReferencePromoterView.as_view(),
        name="set-reference-promoter",
    ),
    path("request_signatures", views.DoctorateAdmissionRequestSignaturesView.as_view(), name="request-signatures"),
    path('remove-member/<type>/<matricule>', views.DoctorateAdmissionRemoveActorView.as_view(), name='remove-actor'),
    path('approve-by-pdf', views.DoctorateAdmissionApprovalByPdfView.as_view(), name='approve-by-pdf'),
    path("update/", include((update_paths, "update"))),
    path("cancel", views.DoctorateAdmissionCancelView.as_view(), name="cancel"),
    path("confirm", views.DoctorateAdmissionConfirmFormView.as_view(), name="confirm"),
    path("accounting", views.DoctorateAdmissionAccountingDetailView.as_view(), name="accounting"),
    path("confirmation", views.DoctorateAdmissionConfirmationPaperDetailView.as_view(), name="confirmation-paper"),
    path(
        "confirmation-paper-canvas",
        views.DoctorateAdmissionConfirmationPaperCanvasExportView.as_view(),
        name="confirmation-paper-canvas",
    ),
    path("extension-request", views.DoctorateAdmissionExtensionRequestDetailView.as_view(), name="extension-request"),
    path("doctoral-training", views.DoctoralTrainingListView.as_view(), name="doctoral-training"),
    path("doctoral-training/", include((training_paths, "doctoral-training"))),
    path("complementary-training", views.ComplementaryTrainingListView.as_view(), name="complementary-training"),
    path("complementary-training/", include((training_paths, "complementary-training"))),
    path("course-enrollment", views.CourseEnrollmentListView.as_view(), name="course-enrollment"),
    path("course-enrollment/", include((training_paths, "course-enrollment"))),
    path("training", views.DoctorateAdmissionTrainingView.as_view(), name="training"),
    path("training/", include((training_paths, "training"))),
    path("training-choice", views.AdmissionTrainingChoiceFormView.as_view(), name="training-choice"),
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
        RedirectView.as_view(pattern_name="admission:doctorate-create:training-choice"),
        name="doctorate-create",
    ),
    path("doctorate/create/", include((creation_paths, "doctorate-create"))),
    # Detail
    path("doctorate/<uuid:pk>/", views.redirect_detail, name="doctorate"),
    path("doctorate/<uuid:pk>/", include((doctorate_paths, "doctorate"))),
]
