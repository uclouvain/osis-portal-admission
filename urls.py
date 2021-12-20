# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.module_loading import import_string
from django.views.generic import RedirectView

from .contrib import views

app_name = "admission"


def generate_tab_urls(pattern_prefix, view_suffix, name, create_only=False, detail_only=False):
    """Generates tab urls for a each action, views must exists"""
    tab_names = ["project", "person", "coordonnees", "education", "languages"]
    # pattern_names = ["person", "details", "education", "curriculum", "project"]
    if not create_only:
        tab_names += [
            "cotutelle",
            "supervision",
            # "confirm",
            # "confirm-paper",
            # "training",
            # "jury",
            # "private-defense",
            # "public-defense",
        ]
    # if detail_only:
    #     pattern_names.append('messages')

    # Determine module file to import
    module_path = 'admission.contrib.views.{}_tabs.{{tab}}.{{view}}'.format('detail' if detail_only else 'form')

    # Add pattern for each tab
    includes = [
        path(tab_name, import_string(module_path.format(
            tab=tab_name,
            view='DoctorateAdmission{}{}'.format(tab_name.title().replace('-', ''), view_suffix),
        )).as_view(), name=tab_name)
        for tab_name in tab_names
    ]

    # Some extra actions
    if not create_only:
        includes.append(
            path(
                'remove-member/<type>/<matricule>',
                views.DoctorateAdmissionRemoveActorView.as_view(),
                name='remove-actor'
            )
        )

    return [
        # Add a pattern that redirects to the default tab
        path(pattern_prefix, RedirectView.as_view(pattern_name='admission:{}:project'.format(name)), name=name),
        path(pattern_prefix, include((includes, name))),
    ]


urlpatterns = [
    path("doctorates/", views.DoctorateAdmissionListView.as_view(), name="doctorate-list"),
    path("autocomplete/", include((
        [
            path("tutor/", views.TutorAutocomplete.as_view(), name="tutor"),
            path("person/", views.PersonAutocomplete.as_view(), name="person"),
            path("doctorate/", views.DoctorateAutocomplete.as_view(), name="doctorate"),
            path("country/", views.CountryAutocomplete.as_view(), name="country"),
            path("city/", views.CityAutocomplete.as_view(), name="city"),
            path("language/", views.LanguageAutocomplete.as_view(), name="language"),
        ],
        "autocomplete",
    ))),
    path("doctorates/<uuid:pk>/cancel/", views.DoctorateAdmissionCancelView.as_view(), name="doctorate-cancel"),
    path(
        "doctorates/<uuid:pk>/request_signatures/",
        views.DoctorateAdmissionRequestSignaturesView.as_view(),
        name="doctorate-request-signatures",
    ),
    *generate_tab_urls(
        pattern_prefix='doctorates/create/',
        view_suffix='FormView',
        name='doctorate-create',
        create_only=True,
    ),
    *generate_tab_urls(
        pattern_prefix='doctorates/<uuid:pk>/update/',
        view_suffix='FormView',
        name='doctorate-update',
    ),
    *generate_tab_urls(
        pattern_prefix='doctorates/<pk>/',
        view_suffix='DetailView',
        name='doctorate-detail',
        detail_only=True,
    ),
]
