# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.shortcuts import redirect, render
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import FormView

from admission.contrib.forms.exam import ExamForm
from admission.contrib.views.mixins import LoadDossierViewMixin
from admission.services.mixins import WebServiceFormMixin
from admission.services.person import GeneralEducationAdmissionPersonService

__all__ = [
    'AdmissionExamFormView',
]


class AdmissionExamFormView(LoadDossierViewMixin, WebServiceFormMixin, FormView):
    template_name = "admission/forms/exam.html"
    service_mapping = {
        'general-education': GeneralEducationAdmissionPersonService,
    }
    form_class = ExamForm

    def get(self, request, *args, **kwargs):
        if not self.admission_uuid:
            # Trick template to not display form and buttons
            context = super(LoadDossierViewMixin, self).get_context_data(form=None, **kwargs)
            return render(request, 'admission/forms/need_training_choice.html', context)
        if self.exam['is_valuated'] or not self.exam['required']:
            return redirect(self._get_url('exam', update=False))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.exam['required']:
            return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)

    @cached_property
    def exam(self):
        return (
            self.service_mapping[self.current_context]
            .retrieve_exam(
                person=self.person,
                uuid=self.admission_uuid,
            )
            .to_dict()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["person"] = self.person
        kwargs["is_valuated"] = self.exam['is_valuated']
        if get_language() == settings.LANGUAGE_CODE:
            kwargs['certificate_title'] = self.exam['title_fr']
            kwargs['certificate_help_text'] = self.exam['help_text_fr']
        else:
            kwargs['certificate_title'] = self.exam['title_en']
            kwargs['certificate_help_text'] = self.exam['help_text_en']
        return kwargs

    def get_initial(self):
        return self.exam

    def prepare_data(self, data):
        if not data['year']:
            data['year'] = None
        return data

    def call_webservice(self, data):
        self.service_mapping[self.current_context].update_exam(
            self.person,
            data,
            uuid=self.admission_uuid,
        )
