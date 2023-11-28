# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.conf import settings
from django.urls import include, path

from admission.contrib.views.common.form_tabs.coordonnees import AdmissionCoordonneesFormView
from admission.contrib.views.common.form_tabs.curriculum import AdmissionCurriculumFormView
from admission.contrib.views.common.form_tabs.education import AdmissionEducationFormView
from admission.contrib.views.common.form_tabs.languages import AdmissionLanguagesFormView
from admission.contrib.views.common.form_tabs.person import AdmissionPersonFormView
from admission.contrib.views.common.form_tabs.training_choice import AdmissionTrainingChoiceFormView
from admission.contrib.views.lang import ChangeLanguageView
from osis_common.utils.file_router import FileRouter

app_name = 'admission'

file_router = FileRouter()
urlpatterns = file_router('admission/contrib/views')
# Copy all the common form_tabs to 'admission:create'
urlpatterns += [
    path(
        'create/',
        include(
            (
                [
                    path('person', AdmissionPersonFormView.as_view(), name='person'),
                    path('coordonnees', AdmissionCoordonneesFormView.as_view(), name='coordonnees'),
                    path('training-choice', AdmissionTrainingChoiceFormView.as_view(), name='training-choice'),
                    path('education', AdmissionEducationFormView.as_view(), name='education'),
                    path('curriculum', AdmissionCurriculumFormView.as_view(), name='curriculum'),
                    path('languages', AdmissionLanguagesFormView.as_view(), name='languages'),
                ],
                'create',
            )
        ),
    ),
    path('lang/<str:ui_language>', ChangeLanguageView.as_view(), name=ChangeLanguageView.name),
]

if settings.DEBUG:
    import logging

    logger = logging.getLogger(__name__)
    logger.debug("\n" + file_router.debug(urlpatterns))
