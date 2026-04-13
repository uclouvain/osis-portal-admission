# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext
from django.views import View

from admission.contrib.enums import ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE
from admission.contrib.forms.re_enrolment import ReEnrolmentForm
from admission.services.proposition import AdmissionPropositionService
from frontoffice.settings.osis_sdk.utils import MultipleApiBusinessException

__all__ = ['ReEnrolmentView']


class ReEnrolmentView(View):
    urlpatterns = 're-enrolment'
    http_method_names = ['post']
    create_proposition_method = {
        'general-education': AdmissionPropositionService.create_general_education_proposition,
        # 'continuing-education': AdmissionPropositionService.create_continuing_education_proposition,
        # 'doctorate': AdmissionPropositionService.create_doctorate_proposition,
    }

    def post(self, request, *args, **kwargs):
        form = ReEnrolmentForm(data=request.POST)

        error_message = gettext('An error occured when creating the application.')

        if form.is_valid():
            person = self.request.user.person

            data = {
                'sigle_formation': form.cleaned_data['training_acronym'],
                'annee_formation': form.cleaned_data['training_year'],
                'matricule_candidat': person.global_id,
            }

            admission_context = ADMISSION_CONTEXT_BY_OSIS_EDUCATION_TYPE.get(form.cleaned_data['training_type'])

            create_proposition_method = self.create_proposition_method.get(admission_context)

            try:
                if create_proposition_method:
                    response = create_proposition_method(person=person, data=data)
                    created_uuid = response.get('uuid')
                    messages.info(self.request, gettext('Your data have been saved'))
                    return redirect(f'admission:{admission_context}:update:training-choice', pk=created_uuid)
                else:
                    return redirect('admission:create:training-choice')
            except MultipleApiBusinessException as multiple_business_api_exception:
                error_message = multiple_business_api_exception.exceptions.pop().detail

            except PermissionDenied as exception:
                error_message = str(exception)

        messages.error(request=request, message=error_message)

        return redirect('admission:list')
