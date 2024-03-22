# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.views import View

from admission.services.continuing_education import ContinuingEducationService
from admission.utils import split_training_id

__all__ = [
    'RetrieveContinuingEducationInformationView',
]


class RetrieveContinuingEducationInformationView(LoginRequiredMixin, View):
    name = 'retrieve-continuing-education-information'
    urlpatterns = {
        'retrieve_continuing_education_information': 'retrieve-continuing-education-information',
    }

    def get(self, request, *args, **kwargs):
        training_id = self.request.GET.get('training')

        if training_id:
            training = split_training_id(training_id)

            if len(training) == 2:
                data = ContinuingEducationService.get_continuing_education_information(
                    person=self.request.user.person,
                    acronym=training[0],
                    year=training[1],
                )
                return JsonResponse(data=data.to_dict())
        raise BadRequest
