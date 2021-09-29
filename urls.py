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
from django.views.generic import RedirectView

from .contrib import views

app_name = "admission"


def generate_tab_urls(pattern_prefix, view_suffix, name, create_only=False, detail_only=False):
    """Generates tab urls for a each action, views must exists"""
    pattern_names = ["project"]
    # pattern_names = ["person", "details", "education", "curriculum", "project"]
    if not create_only:
        pattern_names += [
            # "supervision",
            # "confirm",
            # "confirm-paper",
            # "training",
            # "jury",
            # "private-defense",
            # "public-defense",
        ]
    # if detail_only:
    #     pattern_names.append('messages')

    # Add pattern for each tab
    includes = [
        path(pattern_name, getattr(views, 'DoctorateAdmission{}{}'.format(
            pattern_name.title().replace('-', ''),
            view_suffix,
        )).as_view(), name=pattern_name)
        for pattern_name in pattern_names
    ]

    return [
        # Add a pattern that redirects to the default tab
        # TODO change from 'project' to 'person'
        path(pattern_prefix, RedirectView.as_view(pattern_name='admission:{}:project'.format(name)), name=name),
        path(pattern_prefix, include((includes, name))),
    ]


urlpatterns = (
        [
            path("doctorates/", views.DoctorateAdmissionListView.as_view(), name="doctorate-list"),
            path("autocomplete/", include(([
                # path("candidate/", views.CandidateAutocomplete.as_view(), name="candidate"),
                path("sector/", views.SectorAutocomplete.as_view(), name="sector"),
                path("doctorate/", views.DoctorateAutocomplete.as_view(), name="doctorate"),
            ], "autocomplete"))),
        ]
        + generate_tab_urls('doctorates/create/', 'FormView', 'doctorate-create', create_only=True)
        + generate_tab_urls('doctorates/<uuid:pk>/update/', 'FormView', 'doctorate-update')
        + generate_tab_urls('doctorates/<pk>/', 'DetailView', 'doctorate-detail', detail_only=True)
)
